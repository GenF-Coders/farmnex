from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.user import User
from app.models.waste_record import WasteRecord
from app.repositories.waste_record_repository import WasteRecordRepository

# The only fields an owner may change after creation (the schema already limits this; kept as a safety net).
_UPDATABLE = {"waste_type", "quantity", "unit", "reason", "recorded_at"}


class WasteRecordService:
    def __init__(self, repository: WasteRecordRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate_paging(offset: int, limit: int) -> None:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")

    async def create(self, data: dict[str, Any], current_user: User) -> WasteRecord:
        farm = await self.repository.get_farm_owned_by_user(data["farm_id"], current_user.id)
        if farm is None:
            raise NotFoundError("Farm not found.")

        batch_id = None
        if data.get("crop_batch_id") is not None:
            batch = await self.repository.get_batch_owned_on_farm(data["crop_batch_id"], current_user.id, farm.id)
            if batch is None:
                raise NotFoundError("CropBatch not found.")
            batch_id = batch.id

        values = {
            "farm_id": farm.id,
            "crop_batch_id": batch_id,
            "waste_type": data["waste_type"],
            "quantity": data["quantity"],
            "unit": data["unit"],
            "reason": data.get("reason"),
            "recorded_at": data.get("recorded_at") or datetime.now(timezone.utc),
            "recorded_by_id": current_user.id,  # server-owned: from the login token
            "status": "ACTIVE",  # server-owned
        }
        return await self.repository.create(**values)

    async def get(self, public_id: UUID, current_user: User) -> WasteRecord:
        entity = await self.repository.get_owned_by_public_id(public_id, current_user.id)
        if entity is None:
            raise NotFoundError("WasteRecord not found.")
        return entity

    async def list(
        self, offset: int = 0, limit: int = 100, *, current_user: User | None = None
    ) -> tuple[list[WasteRecord], int]:
        """Your own records. Without `current_user` it returns every row: that path exists only because
        `me_service` (the dashboard) still calls it that way and filters afterwards; no route uses it."""
        self._validate_paging(offset, limit)
        if current_user is None:
            return await self.repository.list_all(offset=offset, limit=limit), await self.repository.count_all()
        return (
            await self.repository.list_owned(user_id=current_user.id, offset=offset, limit=limit),
            await self.repository.count_owned(user_id=current_user.id),
        )

    async def update(self, public_id: UUID, data: dict[str, Any], current_user: User) -> WasteRecord:
        entity = await self.get(public_id, current_user)
        clean = {key: value for key, value in data.items() if key in _UPDATABLE and value is not None}
        if clean.get("unit") is not None and clean["unit"] != entity.unit and await self.repository.count_listings(entity.id):
            raise ConflictError("The unit cannot change while this waste record has listings.")
        largest = await self.repository.max_listing_quantity(entity.id)
        if clean.get("quantity") is not None and largest is not None and clean["quantity"] < largest:
            raise ConflictError("The quantity cannot be lower than the quantity of a listing made from it.")
        return await self.repository.update(entity, **clean)

    async def delete(self, public_id: UUID, current_user: User) -> None:
        entity = await self.get(public_id, current_user)
        if await self.repository.count_listings(entity.id) > 0:
            raise ConflictError("This waste record has listings, so it cannot be deleted.")
        await self.repository.delete(entity)
