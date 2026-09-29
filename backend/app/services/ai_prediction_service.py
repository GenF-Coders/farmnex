from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.models.ai_prediction import AIPrediction
from app.repositories.ai_prediction_repository import AIPredictionRepository


class AIPredictionService:
    def __init__(self, repository: AIPredictionRepository) -> None:
        self.repository = repository

    async def create(self, data: dict[str, Any]) -> AIPrediction:
        return await self.repository.create(**data)

    async def get(self, public_id: UUID) -> AIPrediction:
        entity = await self.repository.get_by_public_id(public_id)
        if entity is None:
            raise NotFoundError("AIPrediction not found.")
        return entity

    async def list(self, offset: int = 0, limit: int = 100) -> tuple[list[AIPrediction], int]:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")
        return await self.repository.list(offset=offset, limit=limit), await self.repository.count()

    async def update(self, public_id: UUID, data: dict[str, Any]) -> AIPrediction:
        entity = await self.get(public_id)
        protected = {"id", "public_id", "created_at", "updated_at"}
        clean = {k: v for k, v in data.items() if k not in protected}
        return await self.repository.update(entity, **clean)

    async def delete(self, public_id: UUID) -> None:
        entity = await self.get(public_id)
        await self.repository.delete(entity)
