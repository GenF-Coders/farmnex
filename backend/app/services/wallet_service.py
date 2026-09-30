from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID, uuid4

from app.core.exceptions import ConflictError, NotFoundError
from app.models.bid import Bid
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.models.wallet_ledger import WalletLedgerEntry
from app.repositories.order_repository import OrderRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.order_service import SHIPPED_ITEM_STATUSES, OrderService

logger = logging.getLogger(__name__)

# F12 / S20 demo wallet. No real gateway: "Pay (demo)" only writes the ledger. Rules (Atharv):
# - accepting a bid holds 20% of the order from the buyer (the advance);
# - the buyer pays the rest with Pay (demo) any time before delivery;
# - on delivery (S26) everything held for the order goes to the farmer, once;
# - a PLACED order with nothing paid after 30 minutes is cancelled (stock goes back); a paid one never;
# - money held on a cancelled order goes back to the buyer.
DEMO_PROVIDER = "DEMO"
BID_ADVANCE_SHARE = Decimal("0.20")
UNPAID_ORDER_MINUTES = 30
# Only orders placed after S20 was built expire: older ones could never be paid (no Pay route yet),
# so the first timer run must not cancel rows that are already in the live database.
EXPIRY_STARTS_AT = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)
# Orders made by accepting a bid (S19: order_number "BID-...") never expire - they have the advance.
BID_ORDER_PREFIX = "BID-"
TIMER_SECONDS = 300
PAYABLE_ORDER_STATUSES = {"PLACED", "CONFIRMED"}
MONEY = Decimal("0.01")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, ROUND_HALF_UP)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class WalletService:
    """All money moves go through here, inside the caller's transaction."""

    def __init__(self, repository: WalletRepository) -> None:
        self.repository = repository
        self.payments = PaymentRepository(repository.db)

    async def _hold(
        self, order: Order, amount: Decimal, *, key: str, method: str,
        bid: Bid | None = None, request_key: str | None = None,
    ) -> Payment | None:
        """HOLD `amount` from the order's buyer and record a HELD demo payment. None if `key` was
        already used (nothing is written twice)."""
        payment_public_id = uuid4()
        buyer = await self.repository.get_user(order.buyer_id)
        entry = await self.repository.add_entry(
            user_public_id=buyer.public_id,
            order_public_id=order.public_id,
            bid_public_id=bid.public_id if bid is not None else None,
            payment_public_id=payment_public_id,
            entry_type="HOLD",
            amount=amount,
            currency=order.currency,
            idempotency_key=key,
            request_key=request_key,
        )
        if entry is None:
            return None
        return await self.payments.create(
            public_id=payment_public_id,
            order_id=order.id,
            payer_id=order.buyer_id,  # from the order, never from a request
            provider=DEMO_PROVIDER,
            provider_payment_id=f"DEMO-{payment_public_id.hex[:16].upper()}",
            amount=amount,
            currency=order.currency,
            status="HELD",
            payment_method=method,
            paid_at=_now(),
        )

    # --- Bid accept (called by BidService.accept) ----------------------------------------------

    async def hold_bid_advance(self, order: Order, bid: Bid, *, request_key: str | None = None) -> None:
        """Hold 20% of the winning bid's order. Once per bid, however often accept is repeated."""
        amount = max(_money(order.total_amount * BID_ADVANCE_SHARE), MONEY)
        await self._hold(order, amount, key=f"HOLD:BID:{bid.public_id}", method="BID_ADVANCE_20",
                         bid=bid, request_key=request_key)

    # --- Pay (demo) -----------------------------------------------------------------------------

    async def pay_demo(
        self, order_public_id: UUID, current_user: User, *, request_key: str | None = None
    ) -> tuple[Payment, UUID]:
        """The order's buyer pays what is still due (total minus what is already held). Paying
        again returns the same payment. Anyone else gets 404."""
        order = await self.repository.lock_order(order_public_id, buyer_id=current_user.id)
        if order is None:
            raise NotFoundError("Order not found.")
        if order.status not in PAYABLE_ORDER_STATUSES:
            raise ConflictError("This order can't be paid.")

        held = await self.repository.held_for_order(order.public_id)
        if held == 0 and _is_expired(order):
            raise ConflictError("This order expired because it wasn't paid within 30 minutes.")
        due = _money(order.total_amount - held)
        if due > 0:
            payment = await self._hold(order, due, key=f"HOLD:PAY:{order.public_id}", method="DEMO",
                                       request_key=request_key)
            if payment is not None:
                return payment, order.public_id
        # Already paid in full: return the payment made earlier.
        payment = await self.repository.latest_payment(order.id, {"HELD", "RELEASED"})
        if payment is None:
            raise ConflictError("This order has nothing left to pay.")
        return payment, order.public_id

    # --- Delivery (S26) and refunds ---------------------------------------------------------------

    async def release_for_order(self, order_public_id: UUID) -> Decimal | None:
        """Give everything held for a DELIVERED order to its farmer. Only once: a second call (or an
        order with nothing held) returns None. Not delivered yet -> ConflictError."""
        order = await self.repository.lock_order(order_public_id)
        if order is None:
            raise NotFoundError("Order not found.")
        if order.status != "DELIVERED":
            raise ConflictError("Money is released only when the order is delivered.")
        held = await self.repository.held_for_order(order.public_id)
        if held <= 0:
            return None
        sellers = await self.repository.sellers_of_live_items(order.id)
        if len(sellers) != 1:  # one order = one farmer; only rows from before S18 can mix
            raise ConflictError("This order doesn't have exactly one farmer.")
        # The farmer gets at most the order total (it drops if an item was cancelled after paying);
        # anything held above it goes back to the buyer.
        released = min(held, order.total_amount)
        entry = await self.repository.add_entry(
            user_public_id=sellers[0], order_public_id=order.public_id, entry_type="RELEASE",
            amount=released, currency=order.currency, idempotency_key=f"RELEASE:{order.public_id}",
        ) if released > 0 else None
        extra = held - released
        if extra > 0:
            buyer = await self.repository.get_user(order.buyer_id)
            await self.repository.add_entry(
                user_public_id=buyer.public_id, order_public_id=order.public_id, entry_type="REFUND",
                amount=extra, currency=order.currency, idempotency_key=f"REFUND:EXTRA:{order.public_id}",
            )
        if entry is None:
            if extra > 0:  # nothing left to release (every item cancelled): it all went back
                await self.repository.set_payment_status(order.id, from_status="HELD", to_status="REFUNDED")
            return None
        await self.repository.set_payment_status(order.id, from_status="HELD", to_status="RELEASED")
        return released

    async def refund_if_cancelled(self, order_public_id: UUID) -> Decimal | None:
        """Give money held on a CANCELLED order back to the buyer, once."""
        order = await self.repository.lock_order(order_public_id)
        if order is None or order.status != "CANCELLED":
            return None
        held = await self.repository.held_for_order(order.public_id)
        if held <= 0:
            return None
        buyer = await self.repository.get_user(order.buyer_id)
        entry = await self.repository.add_entry(
            user_public_id=buyer.public_id, order_public_id=order.public_id, entry_type="REFUND",
            amount=held, currency=order.currency, idempotency_key=f"REFUND:{order.public_id}",
        )
        if entry is None:
            return None
        await self.repository.set_payment_status(order.id, from_status="HELD", to_status="REFUNDED")
        return held

    # --- 30-minute expiry ------------------------------------------------------------------------

    async def expire_if_unpaid(self, order_public_id: UUID, now: datetime | None = None) -> bool:
        """Cancel a PLACED order that is over 30 minutes old and has nothing paid, through S18's
        cancel (stock goes back). Re-checked under the order lock, so a payment that got in first wins."""
        order = await self.repository.lock_order(order_public_id)
        if order is None or order.status != "PLACED" or not _is_expired(order, now):
            return False
        if await self.repository.held_for_order(order.public_id) != 0:
            return False
        order_repository = OrderRepository(self.repository.db)
        if await order_repository.has_items_in(order.id, SHIPPED_ITEM_STATUSES):
            return False  # already on its way; S18's cancel would refuse it anyway
        buyer = await self.repository.get_user(order.buyer_id)
        await OrderService(order_repository).update(
            order.public_id, {"status": "CANCELLED"}, buyer
        )
        return True

    # --- My wallet -----------------------------------------------------------------------------

    async def summary(self, current_user: User) -> dict:
        totals = await self.repository.totals_for_user(current_user.public_id)
        entries = await self.repository.entries_for_user(current_user.public_id)
        return {
            "held_from_me": await self.repository.held_on_orders(buyer_id=current_user.id),
            "held_for_me": await self.repository.held_on_orders(seller_id=current_user.id),
            "received": totals.get("RELEASE", Decimal("0")),
            "refunded": totals.get("REFUND", Decimal("0")),
            "entries": [_entry_view(entry) for entry in entries],
        }


def _is_expired(order: Order, now: datetime | None = None) -> bool:
    placed = order.placed_at or order.created_at
    return (
        order.status == "PLACED"
        and not order.order_number.startswith(BID_ORDER_PREFIX)
        and placed is not None
        and EXPIRY_STARTS_AT <= placed < (now or _now()) - timedelta(minutes=UNPAID_ORDER_MINUTES)
    )


def _entry_view(entry: WalletLedgerEntry) -> dict:
    return {
        "public_id": entry.public_id,
        "entry_type": entry.entry_type,
        "amount": entry.amount,
        "currency": entry.currency,
        "order_id": entry.order_public_id,
        "bid_id": entry.bid_public_id,
        "payment_id": entry.payment_public_id,
        "created_at": entry.created_at,
    }


# --- Jobs with their own database session (the timer, and S26's delivery listener) -------------


async def release_for_order(order_public_id: UUID) -> Decimal | None:
    """For S26: after the order is DELIVERED (committed), give the held money to the farmer - once.
    Opens its own session and commits. Returns the amount released, or None if nothing was released."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        try:
            amount = await WalletService(WalletRepository(session)).release_for_order(order_public_id)
            await session.commit()
            return amount
        except Exception:
            await session.rollback()
            raise


async def _one_order_each(order_ids: list[UUID], job_name: str, step) -> int:
    """Run `step(service, order_id)` in its own transaction per order, so one bad order can't stop
    the rest. Returns how many returned something truthy."""
    from app.core.database import AsyncSessionLocal

    done = 0
    for order_id in order_ids:
        async with AsyncSessionLocal() as session:
            try:
                if await step(WalletService(WalletRepository(session)), order_id):
                    done += 1
                await session.commit()
            except Exception:
                await session.rollback()
                logger.exception("Wallet %s failed for order %s", job_name, order_id)
    return done


async def run_wallet_jobs(now: datetime | None = None) -> tuple[int, int]:
    """Cancel unpaid PLACED orders older than 30 minutes, then refund money held on cancelled
    orders. Safe to run from several workers at once. Returns (expired, refunded)."""
    from app.core.database import AsyncSessionLocal

    now = now or _now()
    async with AsyncSessionLocal() as session:
        repository = WalletRepository(session)
        unpaid = await repository.unpaid_placed_orders(
            now - timedelta(minutes=UNPAID_ORDER_MINUTES),
            placed_after=EXPIRY_STARTS_AT,
            skip_order_prefix=BID_ORDER_PREFIX,
        )
    expired = await _one_order_each(unpaid, "expiry", lambda s, order_id: s.expire_if_unpaid(order_id, now))

    async with AsyncSessionLocal() as session:
        cancelled = await WalletRepository(session).cancelled_orders_with_money_held()
    refunded = await _one_order_each(cancelled, "refund", lambda s, order_id: s.refund_if_cancelled(order_id))
    if expired or refunded:
        logger.info("Wallet jobs: %s unpaid orders expired, %s cancelled orders refunded", expired, refunded)
    return expired, refunded


_timer_task: asyncio.Task | None = None


async def _timer_loop() -> None:
    while True:
        try:
            await run_wallet_jobs()
        except Exception:  # keep the timer alive; the next round tries again
            logger.exception("Wallet jobs failed")
        await asyncio.sleep(TIMER_SECONDS)


def start_wallet_timer() -> None:
    """Called once at startup (main.py): run the wallet jobs every 5 minutes."""
    global _timer_task
    if _timer_task is None or _timer_task.done():
        _timer_task = asyncio.get_running_loop().create_task(_timer_loop())


def stop_wallet_timer() -> None:
    global _timer_task
    if _timer_task is not None:
        _timer_task.cancel()
        _timer_task = None
