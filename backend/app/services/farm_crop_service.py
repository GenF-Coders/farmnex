from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.farm_crop import FarmCrop
from app.models.user import User
from app.repositories.farm_crop_repository import FarmCropRepository


class FarmCropService:
    def __init__(self, repository: FarmCropRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate_paging(offset: int, limit: int) -> None:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")

    async def create(self, data: dict[str, Any], current_user: User) -> FarmCrop:
        farm_public_id = data.pop("farm_id")
        crop_type_public_id = data.pop("crop_type_id")

        farm = await self.repository.get_farm_owned_by_user(farm_public_id, current_user.id)
        if farm is None:
            raise ForbiddenError("You do not own this farm, or it is inactive.")

        crop_type = await self.repository.get_active_crop_type(crop_type_public_id)
        if crop_type is None:
            raise NotFoundError("Active crop type not found.")

        values = {
            **data,
            "farmer_id": current_user.id,
            "farm_id": farm.id,
            "crop_type_id": crop_type.id,
        }
        return await self.repository.create(**values)

    async def get(self, public_id: UUID, current_user: User) -> FarmCrop:
        entity = await self.repository.get_owned_by_public_id(public_id, current_user.id)
        if entity is None:
            raise NotFoundError("FarmCrop not found.")
        return entity

    async def list(self, *, current_user: User, offset: int = 0, limit: int = 100) -> tuple[list[FarmCrop], int]:
        self._validate_paging(offset, limit)
        return (
            await self.repository.list_owned(user_id=current_user.id, offset=offset, limit=limit),
            await self.repository.count_owned(user_id=current_user.id),
        )

    async def update(self, public_id: UUID, data: dict[str, Any], current_user: User) -> FarmCrop:
        entity = await self.get(public_id, current_user)

        data.pop("farmer_id", None)
        if "farm_id" in data:
            farm = await self.repository.get_farm_owned_by_user(data.pop("farm_id"), current_user.id)
            if farm is None:
                raise ForbiddenError("You do not own the selected farm, or it is inactive.")
            data["farm_id"] = farm.id

        if "crop_type_id" in data:
            crop_type = await self.repository.get_active_crop_type(data.pop("crop_type_id"))
            if crop_type is None:
                raise NotFoundError("Active crop type not found.")
            data["crop_type_id"] = crop_type.id

        for protected in {"id", "public_id", "farmer_id", "created_at", "updated_at"}:
            data.pop(protected, None)
        return await self.repository.update(entity, **data)

    async def delete(self, public_id: UUID, current_user: User) -> None:
        entity = await self.get(public_id, current_user)
        await self.repository.delete(entity)
