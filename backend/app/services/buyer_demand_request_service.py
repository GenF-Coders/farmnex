from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.models.buyer_demand_request import BuyerDemandRequest
from app.models.user import User
from app.repositories.buyer_demand_request_repository import BuyerDemandRequestRepository

# The only fields the owner may change after creation (the schema already limits this; kept as a safety net).
_UPDATABLE = {
    "title", "description", "quantity", "unit", "target_price",
    "delivery_city", "delivery_state", "needed_by", "status",
}


def _can_see_open(user: User) -> bool:
    """Farmers browse open demand from every buyer."""
    return user.role is not None and user.role.name.upper() == "FARMER"


class BuyerDemandRequestService:
    def __init__(self, repository: BuyerDemandRequestRepository) -> None:
        self.repository = repository

    @staticmethod
    def _validate_paging(offset: int, limit: int) -> None:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")

    async def create(self, data: dict[str, Any], current_user: User) -> BuyerDemandRequest:
        crop_type = await self.repository.get_active_crop_type(data["crop_type_id"])
        if crop_type is None:
            raise NotFoundError("CropType not found.")
        values = {
            "crop_type_id": crop_type.id,
            "title": data["title"],
            "description": data.get("description"),
            "quantity": data["quantity"],
            "unit": data["unit"],
            "target_price": data.get("target_price"),
            "delivery_city": data.get("delivery_city"),
            "delivery_state": data.get("delivery_state"),
            "needed_by": data.get("needed_by"),
            "buyer_id": current_user.id,  # server-owned: from the login token
            "status": "ACTIVE",  # server-owned at creation ("ACTIVE" = open)
        }
        return await self.repository.create(**values)

    async def get(self, public_id: UUID, current_user: User) -> BuyerDemandRequest:
        entity = await self.repository.get_visible_by_public_id(
            public_id, current_user.id, _can_see_open(current_user)
        )
        if entity is None:
            raise NotFoundError("BuyerDemandRequest not found.")
        return entity

    async def list(
        self, offset: int = 0, limit: int = 100, *, current_user: User, only_mine: bool = False
    ) -> tuple[list[BuyerDemandRequest], int]:
        self._validate_paging(offset, limit)
        can_see_open = _can_see_open(current_user)
        return (
            await self.repository.list_visible(
                user_id=current_user.id, can_see_open=can_see_open, only_mine=only_mine, offset=offset, limit=limit
            ),
            await self.repository.count_visible(
                user_id=current_user.id, can_see_open=can_see_open, only_mine=only_mine
            ),
        )

    async def _get_owned(self, public_id: UUID, current_user: User) -> BuyerDemandRequest:
        entity = await self.repository.get_owned_by_public_id(public_id, current_user.id)
        if entity is None:
            raise NotFoundError("BuyerDemandRequest not found.")
        return entity

    async def update(self, public_id: UUID, data: dict[str, Any], current_user: User) -> BuyerDemandRequest:
        entity = await self._get_owned(public_id, current_user)
        clean = {k: v for k, v in data.items() if k in _UPDATABLE and v is not None}
        return await self.repository.update(entity, **clean)

    async def delete(self, public_id: UUID, current_user: User) -> None:
        await self.repository.delete(await self._get_owned(public_id, current_user))
