from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.buyer_demand_request import BuyerDemandRequest


class BuyerDemandRequestRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: int) -> BuyerDemandRequest | None:
        result = await self.db.execute(select(BuyerDemandRequest).where(BuyerDemandRequest.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> BuyerDemandRequest | None:
        result = await self.db.execute(select(BuyerDemandRequest).where(BuyerDemandRequest.public_id == public_id))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[BuyerDemandRequest]:
        result = await self.db.execute(select(BuyerDemandRequest).order_by(BuyerDemandRequest.created_at.desc(), BuyerDemandRequest.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(BuyerDemandRequest))
        return int(result.scalar_one())

    async def create(self, **values: Any) -> BuyerDemandRequest:
        entity = BuyerDemandRequest(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: BuyerDemandRequest, **values: Any) -> BuyerDemandRequest:
        for field, value in values.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: BuyerDemandRequest) -> None:
        await self.db.delete(entity)
        await self.db.flush()
