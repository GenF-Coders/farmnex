from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_recommendation import AIRecommendation


class AIRecommendationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: int) -> AIRecommendation | None:
        result = await self.db.execute(select(AIRecommendation).where(AIRecommendation.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> AIRecommendation | None:
        result = await self.db.execute(select(AIRecommendation).where(AIRecommendation.public_id == public_id))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AIRecommendation]:
        result = await self.db.execute(select(AIRecommendation).order_by(AIRecommendation.created_at.desc(), AIRecommendation.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(AIRecommendation))
        return int(result.scalar_one())

    async def create(self, **values: Any) -> AIRecommendation:
        entity = AIRecommendation(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: AIRecommendation, **values: Any) -> AIRecommendation:
        for field, value in values.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: AIRecommendation) -> None:
        await self.db.delete(entity)
        await self.db.flush()
