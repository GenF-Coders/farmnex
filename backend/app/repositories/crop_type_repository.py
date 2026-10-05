from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crop_type import CropType


class CropTypeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _scope(query, include_inactive: bool):
        return query if include_inactive else query.where(CropType.is_active.is_(True))

    async def get_by_public_id(self, public_id: UUID, *, include_inactive: bool) -> CropType | None:
        query = self._scope(select(CropType).where(CropType.public_id == public_id), include_inactive)
        return (await self.db.execute(query)).scalar_one_or_none()

    async def name_exists(self, name: str, *, exclude_id: int | None = None) -> bool:
        query = select(func.count(CropType.id)).where(func.lower(CropType.name) == name.strip().lower())
        if exclude_id is not None:
            query = query.where(CropType.id != exclude_id)
        return int((await self.db.execute(query)).scalar_one()) > 0

    async def list(self, *, include_inactive: bool, offset: int, limit: int) -> list[CropType]:
        query = self._scope(select(CropType), include_inactive)
        result = await self.db.execute(query.order_by(CropType.name, CropType.id).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self, *, include_inactive: bool) -> int:
        query = self._scope(select(func.count(CropType.id)), include_inactive)
        return int((await self.db.execute(query)).scalar_one())

    async def create(self, **values: Any) -> CropType:
        entity = CropType(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: CropType, **values: Any) -> CropType:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity
