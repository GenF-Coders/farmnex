from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.crop_batch import CropBatch
from app.models.farm import Farm
from app.models.farm_crop import FarmCrop
from app.models.waste_record import WasteRecord
from app.models.waste_utilization_listing import WasteUtilizationListing


class WasteRecordRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _attach_batch_ids(self, entities: list[WasteRecord]) -> None:
        """Set `crop_batch_public_id` on each record so the response can show the batch public id."""
        batch_ids = {e.crop_batch_id for e in entities if e.crop_batch_id is not None}
        found: dict[int, UUID] = {}
        if batch_ids:
            rows = await self.db.execute(select(CropBatch.id, CropBatch.public_id).where(CropBatch.id.in_(batch_ids)))
            found = {row.id: row.public_id for row in rows}
        for entity in entities:
            entity.crop_batch_public_id = found.get(entity.crop_batch_id) if entity.crop_batch_id is not None else None

    async def get_farm_owned_by_user(self, farm_public_id: UUID, user_id: int) -> Farm | None:
        result = await self.db.execute(select(Farm).where(Farm.public_id == farm_public_id, Farm.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_batch_owned_on_farm(self, batch_public_id: UUID, user_id: int, farm_id: int) -> CropBatch | None:
        result = await self.db.execute(
            select(CropBatch)
            .join(FarmCrop, FarmCrop.id == CropBatch.farm_crop_id)
            .where(
                CropBatch.public_id == batch_public_id,
                FarmCrop.farmer_id == user_id,
                FarmCrop.farm_id == farm_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_listings(self, waste_record_id: int) -> int:
        result = await self.db.execute(
            select(func.count(WasteUtilizationListing.id)).where(
                WasteUtilizationListing.waste_record_id == waste_record_id
            )
        )
        return int(result.scalar_one())

    async def max_listing_quantity(self, waste_record_id: int):
        result = await self.db.execute(
            select(func.max(WasteUtilizationListing.quantity)).where(
                WasteUtilizationListing.waste_record_id == waste_record_id
            )
        )
        return result.scalar_one()

    async def get_owned_by_public_id(self, public_id: UUID, user_id: int) -> WasteRecord | None:
        result = await self.db.execute(
            select(WasteRecord)
            .options(joinedload(WasteRecord.farm))
            .where(WasteRecord.public_id == public_id, WasteRecord.recorded_by_id == user_id)
        )
        entity = result.scalar_one_or_none()
        if entity is not None:
            await self._attach_batch_ids([entity])
        return entity

    async def list_owned(self, *, user_id: int, offset: int, limit: int) -> list[WasteRecord]:
        result = await self.db.execute(
            select(WasteRecord)
            .options(joinedload(WasteRecord.farm))
            .where(WasteRecord.recorded_by_id == user_id)
            .order_by(WasteRecord.created_at.desc(), WasteRecord.id.desc())
            .offset(offset)
            .limit(limit)
        )
        entities = list(result.scalars().all())
        await self._attach_batch_ids(entities)
        return entities

    async def count_owned(self, *, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(WasteRecord.id)).where(WasteRecord.recorded_by_id == user_id)
        )
        return int(result.scalar_one())

    async def list_all(self, *, offset: int, limit: int) -> list[WasteRecord]:
        """Every user's rows. Only for the dashboard, which filters them afterwards (STATUS follow-up)."""
        result = await self.db.execute(
            select(WasteRecord).order_by(WasteRecord.created_at.desc(), WasteRecord.id.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(WasteRecord))
        return int(result.scalar_one())

    async def _reload(self, entity: WasteRecord) -> WasteRecord:
        await self.db.refresh(entity)
        await self.db.refresh(entity, ["farm"])
        await self._attach_batch_ids([entity])
        return entity

    async def create(self, **values: Any) -> WasteRecord:
        entity = WasteRecord(**values)
        self.db.add(entity)
        await self.db.flush()
        return await self._reload(entity)

    async def update(self, entity: WasteRecord, **values: Any) -> WasteRecord:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.db.flush()
        return await self._reload(entity)

    async def delete(self, entity: WasteRecord) -> None:
        await self.db.delete(entity)
        await self.db.flush()
