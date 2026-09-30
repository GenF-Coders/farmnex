from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.waste_record import WasteRecord
from app.models.waste_utilization_listing import WasteUtilizationListing

_WITH_PARTIES = (
    joinedload(WasteUtilizationListing.waste_record),
    joinedload(WasteUtilizationListing.seller),
)


class WasteUtilizationListingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _visible(user_id: int):
        """ACTIVE listings are public to any logged-in user; the seller also sees their own in any status."""
        return or_(WasteUtilizationListing.status == "ACTIVE", WasteUtilizationListing.seller_id == user_id)

    async def get_waste_record_owned_by_user(self, waste_record_public_id: UUID, user_id: int) -> WasteRecord | None:
        result = await self.db.execute(
            select(WasteRecord).where(
                WasteRecord.public_id == waste_record_public_id, WasteRecord.recorded_by_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_visible_by_public_id(self, public_id: UUID, user_id: int) -> WasteUtilizationListing | None:
        result = await self.db.execute(
            select(WasteUtilizationListing)
            .options(*_WITH_PARTIES)
            .where(WasteUtilizationListing.public_id == public_id, self._visible(user_id))
        )
        return result.scalar_one_or_none()

    async def get_owned_by_public_id(self, public_id: UUID, user_id: int) -> WasteUtilizationListing | None:
        result = await self.db.execute(
            select(WasteUtilizationListing)
            .options(*_WITH_PARTIES)
            .where(WasteUtilizationListing.public_id == public_id, WasteUtilizationListing.seller_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_visible(self, *, user_id: int, only_mine: bool, offset: int, limit: int) -> list[WasteUtilizationListing]:
        query = select(WasteUtilizationListing).options(*_WITH_PARTIES)
        query = query.where(WasteUtilizationListing.seller_id == user_id if only_mine else self._visible(user_id))
        result = await self.db.execute(
            query.order_by(WasteUtilizationListing.created_at.desc(), WasteUtilizationListing.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_visible(self, *, user_id: int, only_mine: bool) -> int:
        query = select(func.count(WasteUtilizationListing.id))
        query = query.where(WasteUtilizationListing.seller_id == user_id if only_mine else self._visible(user_id))
        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def _reload(self, entity: WasteUtilizationListing) -> WasteUtilizationListing:
        await self.db.refresh(entity)
        await self.db.refresh(entity, ["waste_record", "seller"])
        return entity

    async def create(self, **values: Any) -> WasteUtilizationListing:
        entity = WasteUtilizationListing(**values)
        self.db.add(entity)
        await self.db.flush()
        return await self._reload(entity)

    async def update(self, entity: WasteUtilizationListing, **values: Any) -> WasteUtilizationListing:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.db.flush()
        return await self._reload(entity)

    async def delete(self, entity: WasteUtilizationListing) -> None:
        await self.db.delete(entity)
        await self.db.flush()
