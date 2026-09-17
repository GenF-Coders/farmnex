from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order_dispute import OrderDispute


class OrderDisputeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: int) -> OrderDispute | None:
        result = await self.db.execute(select(OrderDispute).where(OrderDispute.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> OrderDispute | None:
        result = await self.db.execute(select(OrderDispute).where(OrderDispute.public_id == public_id))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[OrderDispute]:
        result = await self.db.execute(select(OrderDispute).order_by(OrderDispute.created_at.desc(), OrderDispute.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(OrderDispute))
        return int(result.scalar_one())

    async def create(self, **values: Any) -> OrderDispute:
        entity = OrderDispute(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: OrderDispute, **values: Any) -> OrderDispute:
        for field, value in values.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: OrderDispute) -> None:
        await self.db.delete(entity)
        await self.db.flush()
