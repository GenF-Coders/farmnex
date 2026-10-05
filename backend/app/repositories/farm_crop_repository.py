from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.crop_type import CropType
from app.models.farm import Farm
from app.models.farm_crop import FarmCrop


class FarmCropRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_farm_owned_by_user(self, farm_public_id: UUID, user_id: int) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.public_id == farm_public_id,
                Farm.user_id == user_id,
                Farm.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_active_crop_type(self, crop_type_public_id: UUID) -> CropType | None:
        result = await self.db.execute(
            select(CropType).where(
                CropType.public_id == crop_type_public_id,
                CropType.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_owned_by_public_id(self, public_id: UUID, user_id: int) -> FarmCrop | None:
        result = await self.db.execute(
            select(FarmCrop)
            .join(Farm, Farm.id == FarmCrop.farm_id)
            .where(
                FarmCrop.public_id == public_id,
                Farm.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_owned(self, *, user_id: int, offset: int, limit: int) -> list[FarmCrop]:
        result = await self.db.execute(
            select(FarmCrop)
            .join(Farm, Farm.id == FarmCrop.farm_id)
            .where(Farm.user_id == user_id)
            .order_by(FarmCrop.created_at.desc(), FarmCrop.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_owned(self, *, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(FarmCrop.id))
            .join(Farm, Farm.id == FarmCrop.farm_id)
            .where(Farm.user_id == user_id)
        )
        return int(result.scalar_one())

    async def create(self, **values: Any) -> FarmCrop:
        entity = FarmCrop(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: FarmCrop, **values: Any) -> FarmCrop:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: FarmCrop) -> None:
        await self.db.delete(entity)
        await self.db.flush()
