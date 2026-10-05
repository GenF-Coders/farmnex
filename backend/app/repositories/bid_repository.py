from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import exists, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.bid import Bid
from app.models.bid_event import BidEvent
from app.models.order import Order
from app.models.product_listing import ProductListing


def _visible_to(user_id: int):
    """A bid is visible to its bidder and to the creator of the event it was placed on."""
    event_is_mine = exists().where(BidEvent.id == Bid.bid_event_id, BidEvent.created_by_id == user_id)
    return or_(Bid.bidder_id == user_id, event_is_mine)


class BidRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _base_query():
        return select(Bid).options(joinedload(Bid.bid_event), joinedload(Bid.bidder))

    async def get_event_for_bidding(self, event_public_id: UUID, user_id: int, open_status: str) -> BidEvent | None:
        """The event if this user may see it (open, or their own). Locked until the transaction ends,
        so bids on one event are placed one at a time (the minimum-increment check stays true) and the
        creator can't edit, delete or accept while this bid is being placed."""
        result = await self.db.execute(
            select(BidEvent)
            .options(joinedload(BidEvent.listing))
            .where(
                BidEvent.public_id == event_public_id,
                or_(BidEvent.status == open_status, BidEvent.created_by_id == user_id),
            )
            .with_for_update(of=BidEvent)
        )
        return result.unique().scalar_one_or_none()

    async def highest_active_amount(self, event_id: int) -> Decimal | None:
        result = await self.db.execute(
            select(func.max(Bid.amount)).where(Bid.bid_event_id == event_id, Bid.status == "ACTIVE")
        )
        return result.scalar_one()

    # --- Accept (F12 / S19) ---------------------------------------------------------------

    async def get_for_accept(self, public_id: UUID, creator_id: int) -> Bid | None:
        """A bid on an event this user created, with the event row locked until the transaction
        ends: two accepts (or an accept and a new bid) on one event run one after the other."""
        found = (await self.db.execute(
            select(Bid.id, Bid.bid_event_id)
            .join(BidEvent, BidEvent.id == Bid.bid_event_id)
            .where(Bid.public_id == public_id, BidEvent.created_by_id == creator_id)
        )).one_or_none()
        if found is None:
            return None
        # Lock the event and read it in its own query: after waiting for another accept, Postgres
        # returns the event as that accept left it (a joined copy in one big query would be stale).
        await self.db.execute(
            select(BidEvent)
            .options(joinedload(BidEvent.listing))
            .where(BidEvent.id == found.bid_event_id)
            .with_for_update(of=BidEvent)
            .execution_options(populate_existing=True)
        )
        # Only now read the bid (a new statement sees everything committed before the lock).
        result = await self.db.execute(
            select(Bid)
            .options(joinedload(Bid.bid_event).joinedload(BidEvent.listing), joinedload(Bid.bidder))
            .where(Bid.id == found.id)
            .execution_options(populate_existing=True)
        )
        return result.unique().scalar_one()

    async def lock_listing(self, listing_id: int) -> ProductListing:
        """Lock the listing row and re-read it, so its stock is the current number, not the copy
        loaded with the event before the lock."""
        result = await self.db.execute(
            select(ProductListing)
            .where(ProductListing.id == listing_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return result.scalar_one()

    async def reload(self, bid: Bid) -> Bid:
        await self.db.refresh(bid)
        await self.db.refresh(bid, ["bid_event", "bidder"])
        return bid

    async def get_order_by_number(self, order_number: str, buyer_id: int) -> Order | None:
        result = await self.db.execute(
            select(Order).where(Order.order_number == order_number, Order.buyer_id == buyer_id)
        )
        return result.scalar_one_or_none()

    async def mark_winner(self, event: BidEvent, winner: Bid, *, closed_status: str) -> None:
        """Close the event, set its winner, and mark the winning bid WON and the other open bids LOST."""
        event.status = closed_status
        event.winner_bid_id = winner.id
        winner.status = "WON"
        await self.db.execute(
            update(Bid)
            .where(Bid.bid_event_id == event.id, Bid.id != winner.id, Bid.status == "ACTIVE")
            .values(status="LOST")
        )
        await self.db.flush()
        await self.db.refresh(event)
        await self.db.refresh(event, ["listing"])
        await self.db.refresh(winner)
        await self.db.refresh(winner, ["bid_event", "bidder"])

    async def get_visible_by_public_id(self, public_id: UUID, user_id: int) -> Bid | None:
        result = await self.db.execute(
            self._base_query().where(Bid.public_id == public_id, _visible_to(user_id))
        )
        return result.unique().scalar_one_or_none()

    @staticmethod
    def _visible_condition(user_id: int, bid_event_public_id: UUID | None):
        conditions = [_visible_to(user_id)]
        if bid_event_public_id is not None:
            conditions.append(
                Bid.bid_event_id == select(BidEvent.id).where(BidEvent.public_id == bid_event_public_id).scalar_subquery()
            )
        return conditions

    async def list_visible(
        self, *, user_id: int, bid_event_public_id: UUID | None = None, offset: int = 0, limit: int = 100
    ) -> list[Bid]:
        result = await self.db.execute(
            self._base_query()
            .where(*self._visible_condition(user_id, bid_event_public_id))
            .order_by(Bid.created_at.desc(), Bid.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def count_visible(self, *, user_id: int, bid_event_public_id: UUID | None = None) -> int:
        result = await self.db.execute(
            select(func.count(Bid.id)).where(*self._visible_condition(user_id, bid_event_public_id))
        )
        return int(result.scalar_one())

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[Bid]:
        result = await self.db.execute(select(Bid).order_by(Bid.created_at.desc(), Bid.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Bid))
        return int(result.scalar_one())

    async def create(self, **values: Any) -> Bid:
        entity = Bid(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        await self.db.refresh(entity, ["bid_event", "bidder"])
        return entity
