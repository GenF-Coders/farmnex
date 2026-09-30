from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.bid import Bid
from app.models.bid_event import BidEvent
from app.models.product_listing import ProductListing

# "Open for bids". The table default and the home feed (home_service) both use ACTIVE for this.
OPEN_STATUS = "ACTIVE"
# After the farmer accepts a bid (F12 / S19).
CLOSED_STATUS = "CLOSED"


def _visible_to(user_id: int):
    """Open events on an active listing are public to any logged-in user; the creator also sees
    their own in any status."""
    listing_is_active = exists().where(ProductListing.id == BidEvent.listing_id, ProductListing.status == "ACTIVE")
    return or_(and_(BidEvent.status == OPEN_STATUS, listing_is_active), BidEvent.created_by_id == user_id)


class BidEventRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _base_query():
        return select(BidEvent).options(joinedload(BidEvent.listing))

    async def attach_winner_public_ids(self, events: list[BidEvent]) -> list[BidEvent]:
        """Responses show the winning bid as its public UUID (`winner_bid_public_id`), never the
        internal row id. One query for the whole page."""
        winner_ids = {e.winner_bid_id for e in events if e.winner_bid_id is not None}
        public_ids: dict[int, UUID] = {}
        if winner_ids:
            result = await self.db.execute(select(Bid.id, Bid.public_id).where(Bid.id.in_(winner_ids)))
            public_ids = {row.id: row.public_id for row in result}
        for event in events:
            event.winner_bid_public_id = public_ids.get(event.winner_bid_id)
        return events

    async def get_listing_owned_by_user(self, listing_public_id: UUID, user_id: int) -> ProductListing | None:
        result = await self.db.execute(
            select(ProductListing).where(
                ProductListing.public_id == listing_public_id, ProductListing.seller_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_visible_by_public_id(self, public_id: UUID, user_id: int) -> BidEvent | None:
        result = await self.db.execute(
            self._base_query().where(BidEvent.public_id == public_id, _visible_to(user_id))
        )
        entity = result.unique().scalar_one_or_none()
        if entity is not None:
            await self.attach_winner_public_ids([entity])
        return entity

    async def get_owned_by_public_id(self, public_id: UUID, user_id: int) -> BidEvent | None:
        # Locked, so a bid can't slip in between "has no bids?" and the change (bids take a share lock).
        result = await self.db.execute(
            self._base_query()
            .where(BidEvent.public_id == public_id, BidEvent.created_by_id == user_id)
            .with_for_update(of=BidEvent)
        )
        return result.unique().scalar_one_or_none()

    async def has_bids(self, event_id: int) -> bool:
        result = await self.db.execute(select(exists().where(Bid.bid_event_id == event_id)))
        return bool(result.scalar_one())

    async def list_visible(self, *, user_id: int, only_mine: bool, offset: int, limit: int) -> list[BidEvent]:
        condition = BidEvent.created_by_id == user_id if only_mine else _visible_to(user_id)
        result = await self.db.execute(
            self._base_query()
            .where(condition)
            .order_by(BidEvent.created_at.desc(), BidEvent.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return await self.attach_winner_public_ids(list(result.unique().scalars().all()))

    async def count_visible(self, *, user_id: int, only_mine: bool) -> int:
        condition = BidEvent.created_by_id == user_id if only_mine else _visible_to(user_id)
        result = await self.db.execute(select(func.count(BidEvent.id)).where(condition))
        return int(result.scalar_one())

    async def create(self, **values: Any) -> BidEvent:
        entity = BidEvent(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        await self.db.refresh(entity, ["listing"])
        await self.attach_winner_public_ids([entity])
        return entity

    async def update(self, entity: BidEvent, **values: Any) -> BidEvent:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        await self.db.refresh(entity, ["listing"])
        await self.attach_winner_public_ids([entity])
        return entity

    async def delete(self, entity: BidEvent) -> None:
        await self.db.delete(entity)
        await self.db.flush()
