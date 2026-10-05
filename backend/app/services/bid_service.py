from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.bid import Bid
from app.models.user import User
from app.models.bid_event import BidEvent
from app.models.order import Order
from app.repositories.bid_event_repository import CLOSED_STATUS, OPEN_STATUS, BidEventRepository
from app.repositories.bid_repository import BidRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.order_service import OrderLine, OrderService
from app.services.wallet_service import WalletService


def bid_order_number(bid: Bid) -> str:
    """The order an accepted bid creates is numbered after the bid. order_number is unique, so the
    database itself refuses a second order for the same bid."""
    return f"BID-{bid.public_id.hex.upper()}"


class BidService:
    """Bids can only be placed and read over HTTP. There is no edit or delete: a bid is WON or LOST
    only when the event's farmer accepts a bid (`accept`, F12 / S19)."""

    def __init__(self, repository: BidRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate_paging(offset: int, limit: int) -> None:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")

    async def create(self, data: dict[str, Any], current_user: User) -> Bid:
        event = await self.repository.get_event_for_bidding(data.pop("bid_event_id"), current_user.id, OPEN_STATUS)
        if event is None:
            raise NotFoundError("BidEvent not found.")
        if event.created_by_id == current_user.id or event.listing.seller_id == current_user.id:
            raise ForbiddenError("You cannot bid on your own listing.")
        now = datetime.now(timezone.utc)
        if event.status != OPEN_STATUS or event.listing.status != "ACTIVE" or not (event.starts_at <= now <= event.ends_at):
            raise ConflictError("This event is not open for bids right now.")
        if data["amount"] < event.starting_price:
            raise ValidationError("The bid is below the starting price.")
        # The event row is locked (get_event_for_bidding), so no other bid can slip in between.
        highest = await self.repository.highest_active_amount(event.id)
        if highest is not None and data["amount"] < highest + event.minimum_increment:
            raise ValidationError(
                f"Your bid must be at least {highest + event.minimum_increment} "
                f"(the highest bid {highest} + {event.minimum_increment})."
            )
        if data.get("quantity") is not None and data["quantity"] > event.listing.available_quantity:
            raise ValidationError(
                f"Only {event.listing.available_quantity} {event.listing.unit} is on offer."
            )

        values = {
            **data,
            "bid_event_id": event.id,
            "bidder_id": current_user.id,  # from the login, never the body
            "status": "ACTIVE",  # server-owned
            "placed_at": now,  # server-owned
        }
        return await self.repository.create(**values)

    async def get(self, public_id: UUID, current_user: User) -> Bid:
        entity = await self.repository.get_visible_by_public_id(public_id, current_user.id)
        if entity is None:
            raise NotFoundError("Bid not found.")
        return entity

    async def list(
        self,
        offset: int = 0,
        limit: int = 100,
        *,
        current_user: User | None = None,
        bid_event_id: UUID | None = None,
    ) -> tuple[list[Bid], int]:
        self._validate_paging(offset, limit)
        if current_user is None:
            # Internal callers only (me_service filters the result by bidder itself). The HTTP
            # controller always passes current_user.
            return await self.repository.list(offset=offset, limit=limit), await self.repository.count()
        return (
            await self.repository.list_visible(
                user_id=current_user.id, bid_event_public_id=bid_event_id, offset=offset, limit=limit
            ),
            await self.repository.count_visible(user_id=current_user.id, bid_event_public_id=bid_event_id),
        )

    # --- Accept (F12 / S19) ------------------------------------------------------------------

    async def accept(
        self, public_id: UUID, current_user: User, *, idempotency_key: str | None = None
    ) -> tuple[BidEvent, Bid, Order]:
        """The farmer who created the event accepts one bid (any time while it is open). In one
        transaction: the event closes with this bid as winner, the other open bids are LOST, and the
        winning buyer gets one PLACED order for the bid's quantity at the bid price (amount = price
        per unit).

        Repeating it for the same bid returns the same event, bid and order (so a repeated
        `Idempotency-Key` gets the same result); another bid after a winner is chosen gets 409.
        The same transaction holds 20% of the order from the buyer (S20 wallet). The ledger's own key
        is made from the bid, so the advance is held once however often accept is called;
        `idempotency_key` is only stored next to it for tracing.
        """
        bid = await self.repository.get_for_accept(public_id, current_user.id)
        if bid is None:
            raise NotFoundError("Bid not found.")
        event = bid.bid_event
        order_repository = OrderRepository(self.repository.db)

        if event.winner_bid_id is not None:
            if event.winner_bid_id != bid.id:
                raise ConflictError("A bid on this event was already accepted.")
            order = await self.repository.get_order_by_number(bid_order_number(bid), bid.bidder_id)
            if order is None:  # only possible for rows made before S19
                raise ConflictError("This bid was accepted, but its order was not found.")
            # Re-read the bid: if this request waited for the first accept, the copy is from before it.
            return await self._with_winner(event), await self.repository.reload(bid), order

        if event.status != OPEN_STATUS:
            raise ConflictError("This event is closed.")
        if bid.status != "ACTIVE":
            raise ConflictError("This bid can no longer be accepted.")
        if bid.quantity is None:  # only bids made before S19 (quantity is required now)
            raise ConflictError("This bid has no quantity, so it can't be accepted.")
        if await order_repository.get_buyer_address(bid.bidder_id, None) is None:
            raise ConflictError("The buyer of this bid has not added a delivery address yet.")

        # Lock the listing and re-read its stock now, so create_orders (same transaction, same row)
        # checks and lowers the current number - two accepts or a cancel can't overwrite each other.
        listing = await self.repository.lock_listing(event.listing_id)
        _, [order] = await OrderService(order_repository).create_orders(
            bid.bidder,
            [OrderLine(listing.public_id, bid.quantity, unit_price=bid.amount)],
            from_accepted_bid=True,
        )
        order = await order_repository.update(order, order_number=bid_order_number(bid))
        await WalletService(WalletRepository(self.repository.db)).hold_bid_advance(
            order, bid, request_key=idempotency_key
        )

        await self.repository.mark_winner(event, bid, closed_status=CLOSED_STATUS)
        return await self._with_winner(event), bid, order

    async def _with_winner(self, event: BidEvent) -> BidEvent:
        [event] = await BidEventRepository(self.repository.db).attach_winner_public_ids([event])
        return event
