from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.models.user import User
from app.models.waste_utilization_listing import WasteUtilizationListing
from app.repositories.waste_utilization_listing_repository import WasteUtilizationListingRepository

# The only fields the seller may change after creation (the schema already limits this; kept as a safety net).
_UPDATABLE = {"title", "description", "utilization_type", "quantity", "unit", "price", "status"}


class WasteUtilizationListingService:
    def __init__(self, repository: WasteUtilizationListingRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate_paging(offset: int, limit: int) -> None:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")

    async def create(self, data: dict[str, Any], current_user: User) -> WasteUtilizationListing:
        record = await self.repository.get_waste_record_owned_by_user(data["waste_record_id"], current_user.id)
        if record is None:
            raise NotFoundError("WasteRecord not found.")
        if data["quantity"] > record.quantity:
            raise ValidationError("quantity cannot be more than the quantity of the waste record.")
        if data["unit"] != record.unit:
            raise ValidationError("unit must be the same as the unit of the waste record.")

        values = {
            "waste_record_id": record.id,
            "title": data["title"],
            "description": data.get("description"),
            "utilization_type": data["utilization_type"],
            "quantity": data["quantity"],
            "unit": data["unit"],
            "price": data["price"],
            "seller_id": current_user.id,  # server-owned: from the login token
            "status": "ACTIVE",  # server-owned at creation
        }
        return await self.repository.create(**values)

    async def get(self, public_id: UUID, current_user: User) -> WasteUtilizationListing:
        entity = await self.repository.get_visible_by_public_id(public_id, current_user.id)
        if entity is None:
            raise NotFoundError("WasteUtilizationListing not found.")
        return entity

    async def list(
        self, offset: int = 0, limit: int = 100, *, current_user: User, only_mine: bool = False
    ) -> tuple[list[WasteUtilizationListing], int]:
        self._validate_paging(offset, limit)
        return (
            await self.repository.list_visible(
                user_id=current_user.id, only_mine=only_mine, offset=offset, limit=limit
            ),
            await self.repository.count_visible(user_id=current_user.id, only_mine=only_mine),
        )

    async def _get_owned(self, public_id: UUID, current_user: User) -> WasteUtilizationListing:
        entity = await self.repository.get_owned_by_public_id(public_id, current_user.id)
        if entity is None:
            raise NotFoundError("WasteUtilizationListing not found.")
        return entity

    async def update(self, public_id: UUID, data: dict[str, Any], current_user: User) -> WasteUtilizationListing:
        entity = await self._get_owned(public_id, current_user)
        clean = {key: value for key, value in data.items() if key in _UPDATABLE and value is not None}
        quantity = clean.get("quantity")
        if quantity is not None and quantity > entity.waste_record.quantity:
            raise ValidationError("quantity cannot be more than the quantity of the waste record.")
        if clean.get("unit") is not None and clean["unit"] != entity.waste_record.unit:
            raise ValidationError("unit must be the same as the unit of the waste record.")
        return await self.repository.update(entity, **clean)

    async def delete(self, public_id: UUID, current_user: User) -> None:
        entity = await self._get_owned(public_id, current_user)
        await self.repository.delete(entity)
