from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_prediction import AIPrediction


class AIPredictionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: int) -> AIPrediction | None:
        result = await self.db.execute(select(AIPrediction).where(AIPrediction.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> AIPrediction | None:
        result = await self.db.execute(select(AIPrediction).where(AIPrediction.public_id == public_id))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AIPrediction]:
        result = await self.db.execute(select(AIPrediction).order_by(AIPrediction.created_at.desc(), AIPrediction.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(AIPrediction))
        return int(result.scalar_one())

    async def create(self, **values: Any) -> AIPrediction:
        entity = AIPrediction(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: AIPrediction, **values: Any) -> AIPrediction:
        for field, value in values.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: AIPrediction) -> None:
        await self.db.delete(entity)
        await self.db.flush()
