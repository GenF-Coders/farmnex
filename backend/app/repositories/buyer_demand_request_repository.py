from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.buyer_demand_request import BuyerDemandRequest
from app.models.crop_type import CropType

_WITH_PARTIES = (
    joinedload(BuyerDemandRequest.buyer),
    joinedload(BuyerDemandRequest.crop_type),
)


class BuyerDemandRequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _visible(user_id: int, can_see_open: bool):
        """Your own requests in any status; farmers also see everyone's ACTIVE (open) ones."""
        own = BuyerDemandRequest.buyer_id == user_id
        if not can_see_open:
            return own
        return or_(own, BuyerDemandRequest.status == "ACTIVE")

    async def get_active_crop_type(self, public_id: UUID) -> CropType | None:
        result = await self.db.execute(
            select(CropType).where(CropType.public_id == public_id, CropType.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def get_visible_by_public_id(
        self, public_id: UUID, user_id: int, can_see_open: bool
    ) -> BuyerDemandRequest | None:
        result = await self.db.execute(
            select(BuyerDemandRequest)
            .options(*_WITH_PARTIES)
            .where(BuyerDemandRequest.public_id == public_id, self._visible(user_id, can_see_open))
        )
        return result.scalar_one_or_none()

    async def get_owned_by_public_id(self, public_id: UUID, user_id: int) -> BuyerDemandRequest | None:
        result = await self.db.execute(
            select(BuyerDemandRequest)
            .options(*_WITH_PARTIES)
            .where(BuyerDemandRequest.public_id == public_id, BuyerDemandRequest.buyer_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_visible(
        self, *, user_id: int, can_see_open: bool, only_mine: bool, offset: int, limit: int
    ) -> list[BuyerDemandRequest]:
        condition = (
            BuyerDemandRequest.buyer_id == user_id if only_mine else self._visible(user_id, can_see_open)
        )
        result = await self.db.execute(
            select(BuyerDemandRequest)
            .options(*_WITH_PARTIES)
            .where(condition)
            .order_by(BuyerDemandRequest.created_at.desc(), BuyerDemandRequest.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_visible(self, *, user_id: int, can_see_open: bool, only_mine: bool) -> int:
        condition = (
            BuyerDemandRequest.buyer_id == user_id if only_mine else self._visible(user_id, can_see_open)
        )
        result = await self.db.execute(select(func.count(BuyerDemandRequest.id)).where(condition))
        return int(result.scalar_one())

    async def _reload(self, entity: BuyerDemandRequest) -> BuyerDemandRequest:
        await self.db.refresh(entity)
        await self.db.refresh(entity, ["buyer", "crop_type"])
        return entity

    async def create(self, **values: Any) -> BuyerDemandRequest:
        entity = BuyerDemandRequest(**values)
        self.db.add(entity)
        await self.db.flush()
        return await self._reload(entity)

    async def update(self, entity: BuyerDemandRequest, **values: Any) -> BuyerDemandRequest:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.db.flush()
        return await self._reload(entity)

    async def delete(self, entity: BuyerDemandRequest) -> None:
        await self.db.delete(entity)
        await self.db.flush()
