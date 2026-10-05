from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.crop_type import CropType
from app.models.user import User
from app.repositories.crop_type_repository import CropTypeRepository

_UPDATABLE = {"name", "scientific_name", "description", "category", "default_unit", "is_active"}
_ADMIN_ROLES = {"ADMIN", "SUPER_ADMIN"}


def _is_admin(user: User) -> bool:
    return user.role is not None and user.role.name.upper() in _ADMIN_ROLES


class CropTypeService:
    """Crop types are reference data: everyone logged in reads the active ones, only admins change them.

    The route layer already limits writes to admins; the service checks again so it stays safe if it is
    ever called from somewhere else."""

    def __init__(self, repository: CropTypeRepository) -> None:
        self.repository = repository

    @staticmethod
    def _require_admin(user: User) -> None:
        if not _is_admin(user):
            raise NotFoundError("CropType not found.")

    async def create(self, data: dict[str, Any], current_user: User) -> CropType:
        self._require_admin(current_user)
        if await self.repository.name_exists(data["name"]):
            raise ConflictError("A crop type with this name already exists.")
        try:
            return await self.repository.create(**data, is_active=True)  # server-owned: starts active
        except IntegrityError as exc:
            raise ConflictError("A crop type with this name already exists.") from exc

    async def get(self, public_id: UUID, current_user: User) -> CropType:
        entity = await self.repository.get_by_public_id(public_id, include_inactive=_is_admin(current_user))
        if entity is None:
            raise NotFoundError("CropType not found.")
        return entity

    async def list(
        self, offset: int = 0, limit: int = 100, *, current_user: User
    ) -> tuple[list[CropType], int]:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")
        include_inactive = _is_admin(current_user)
        return (
            await self.repository.list(include_inactive=include_inactive, offset=offset, limit=limit),
            await self.repository.count(include_inactive=include_inactive),
        )

    async def update(self, public_id: UUID, data: dict[str, Any], current_user: User) -> CropType:
        self._require_admin(current_user)
        entity = await self.get(public_id, current_user)
        clean = {k: v for k, v in data.items() if k in _UPDATABLE and v is not None}
        if "name" in clean and await self.repository.name_exists(clean["name"], exclude_id=entity.id):
            raise ConflictError("A crop type with this name already exists.")
        try:
            return await self.repository.update(entity, **clean)
        except IntegrityError as exc:
            raise ConflictError("A crop type with this name already exists.") from exc

    async def delete(self, public_id: UUID, current_user: User) -> None:
        """Retire the crop type (is_active=false). The row stays: farm crops and demand requests use it."""
        self._require_admin(current_user)
        entity = await self.get(public_id, current_user)
        if entity.is_active:
            await self.repository.update(entity, is_active=False)
