from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import case, exists, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from app.models.user import User
from app.models.wallet_ledger import WalletLedgerEntry

# Money still held = HOLDs minus RELEASEs and REFUNDs.
_SIGNED_AMOUNT = case(
    (WalletLedgerEntry.entry_type == "HOLD", WalletLedgerEntry.amount),
    else_=-WalletLedgerEntry.amount,
)


class WalletRepository:
    """Queries for the demo wallet (F12 / S20). Ledger rows are only inserted, never updated."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- Ledger -------------------------------------------------------------------------------

    async def add_entry(self, **values: Any) -> WalletLedgerEntry | None:
        """Insert one ledger row. Returns None (and changes nothing) if a row with the same
        idempotency_key already exists - also when two requests race for it."""
        result = await self.db.execute(
            insert(WalletLedgerEntry)
            .values(**values)
            .on_conflict_do_nothing(index_elements=[WalletLedgerEntry.idempotency_key])
            .returning(WalletLedgerEntry)
        )
        return result.scalar_one_or_none()

    async def held_for_order(self, order_public_id: UUID) -> Decimal:
        result = await self.db.execute(
            select(func.coalesce(func.sum(_SIGNED_AMOUNT), 0)).where(
                WalletLedgerEntry.order_public_id == order_public_id
            )
        )
        return Decimal(result.scalar_one())

    async def totals_for_user(self, user_public_id: UUID) -> dict[str, Decimal]:
        """{entry_type: total} of the rows that belong to this user."""
        result = await self.db.execute(
            select(WalletLedgerEntry.entry_type, func.sum(WalletLedgerEntry.amount))
            .where(WalletLedgerEntry.user_public_id == user_public_id)
            .group_by(WalletLedgerEntry.entry_type)
        )
        return {entry_type: Decimal(total) for entry_type, total in result.all()}

    async def held_on_orders(self, *, buyer_id: int | None = None, seller_id: int | None = None) -> Decimal:
        """Money still held on the orders this user buys (buyer_id) or sells (seller_id)."""
        query = select(func.coalesce(func.sum(_SIGNED_AMOUNT), 0)).join(
            Order, Order.public_id == WalletLedgerEntry.order_public_id
        )
        if buyer_id is not None:
            query = query.where(Order.buyer_id == buyer_id)
        else:
            query = query.where(
                exists().where(OrderItem.order_id == Order.id, OrderItem.seller_id == seller_id)
            )
        return Decimal((await self.db.execute(query)).scalar_one())

    async def entries_for_user(self, user_public_id: UUID, *, limit: int = 50) -> list[WalletLedgerEntry]:
        result = await self.db.execute(
            select(WalletLedgerEntry)
            .where(WalletLedgerEntry.user_public_id == user_public_id)
            .order_by(WalletLedgerEntry.created_at.desc(), WalletLedgerEntry.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # --- Orders -------------------------------------------------------------------------------

    async def lock_order(self, public_id: UUID, *, buyer_id: int | None = None) -> Order | None:
        """The order row, locked until the transaction ends (pay, expire and release wait for each
        other). With buyer_id, only that buyer's order is found."""
        query = select(Order).where(Order.public_id == public_id)
        if buyer_id is not None:
            query = query.where(Order.buyer_id == buyer_id)
        result = await self.db.execute(query.with_for_update(of=Order))
        return result.scalar_one_or_none()

    async def sellers_of_live_items(self, order_id: int) -> list[UUID]:
        """Public ids of the farmers with a not-cancelled item in the order."""
        result = await self.db.execute(
            select(User.public_id)
            .join(OrderItem, OrderItem.seller_id == User.id)
            .where(OrderItem.order_id == order_id, OrderItem.status != "CANCELLED")
            .distinct()
        )
        return list(result.scalars().all())

    async def get_user(self, user_id: int) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def unpaid_placed_orders(
        self, placed_before: datetime, *, placed_after: datetime, skip_order_prefix: str, limit: int = 100
    ) -> list[UUID]:
        """PLACED orders placed between the two times with no HOLD at all (never paid), leaving out
        order numbers that start with `skip_order_prefix`."""
        paid = exists().where(
            WalletLedgerEntry.order_public_id == Order.public_id, WalletLedgerEntry.entry_type == "HOLD"
        )
        placed = func.coalesce(Order.placed_at, Order.created_at)
        result = await self.db.execute(
            select(Order.public_id)
            .where(
                Order.status == "PLACED",
                placed >= placed_after,
                placed < placed_before,
                ~Order.order_number.startswith(skip_order_prefix, autoescape=True),
                ~paid,
            )
            .order_by(Order.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def cancelled_orders_with_money_held(self, *, limit: int = 100) -> list[UUID]:
        result = await self.db.execute(
            select(Order.public_id)
            .join(WalletLedgerEntry, WalletLedgerEntry.order_public_id == Order.public_id)
            .where(Order.status == "CANCELLED")
            .group_by(Order.id, Order.public_id)
            .having(func.sum(_SIGNED_AMOUNT) > 0)
            .order_by(Order.id)
            .limit(limit)
        )
        return list(result.scalars().all())

    # --- Payments -----------------------------------------------------------------------------

    async def latest_payment(self, order_id: int, statuses: set[str]) -> Payment | None:
        result = await self.db.execute(
            select(Payment)
            .where(Payment.order_id == order_id, Payment.status.in_(statuses))
            .order_by(Payment.created_at.desc(), Payment.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def set_payment_status(self, order_id: int, *, from_status: str, to_status: str) -> None:
        await self.db.execute(
            update(Payment)
            .where(Payment.order_id == order_id, Payment.status == from_status)
            .values(status=to_status)
            .execution_options(synchronize_session=False)
        )
