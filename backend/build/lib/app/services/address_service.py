from __future__ import annotations

from typing import Any
from uuid import UUID

from app.models.address import Address
from app.models.user import User
from app.repositories.address_repository import AddressRepository
from app.repositories.farm_repository import FarmRepository
from app.services.exceptions import (
    ConflictError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)


class AddressService:
    """
    Business/application service for addresses.

    Business rules:
        - address always belongs to current user
        - client never controls user_id
        - public UUID is used by API
        - only one active default address per user
        - inactive address cannot be default
        - farm-linked address cannot be deactivated
        - farm-linked address cannot be deleted
        - unknown/protected fields are never persisted

    Transaction rule:
        - this service never commits or rolls back
        - the application/session transaction boundary owns commit/rollback
    """

    def __init__(
        self,
        *,
        address_repository: AddressRepository,
        farm_repository: FarmRepository,
    ) -> None:
        self.address_repository = address_repository
        self.farm_repository = farm_repository

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _clean_create_data(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        allowed_fields = {
            "address_line_1",
            "address_line_2",
            "landmark",
            "village",
            "city",
            "district",
            "state",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "is_default",
        }

        result: dict[str, Any] = {}

        for key, value in data.items():
            if key not in allowed_fields:
                continue

            if isinstance(value, str):
                value = value.strip() or None

            result[key] = value

        return result

    @staticmethod
    def _clean_update_data(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        allowed_fields = {
            "address_line_1",
            "address_line_2",
            "landmark",
            "village",
            "city",
            "district",
            "state",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "is_default",
            "is_active",
        }

        result: dict[str, Any] = {}

        for key, value in data.items():
            if key not in allowed_fields:
                continue

            if isinstance(value, str):
                value = value.strip() or None

            result[key] = value

        return result

    async def _get_owned_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> Address:
        address = await self.address_repository.get_user_address_by_public_id(
            user_id=current_user.id,
            public_id=address_public_id,
        )

        if address is None:
            raise ResourceNotFoundError("Address not found.")

        return address

    async def _is_used_by_farm(self, address_id: int) -> bool:
        farm = await self.farm_repository.get_by_address_id(address_id)
        return farm is not None

    # ============================================================
    # READ
    # ============================================================

    async def get_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> Address:
        return await self._get_owned_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

    async def list_addresses(
        self,
        *,
        current_user: User,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Address], int]:
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")

        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")

        items = await self.address_repository.list_by_user_id(
            user_id=current_user.id,
            active_only=active_only,
            offset=offset,
            limit=limit,
        )

        total = await self.address_repository.count_by_user_id(
            user_id=current_user.id,
            active_only=active_only,
        )

        return items, total

    async def get_default_address(
        self,
        *,
        current_user: User,
    ) -> Address | None:
        return await self.address_repository.get_default_by_user_id(
            current_user.id
        )

    # ============================================================
    # CREATE
    # ============================================================

    async def create_address(
        self,
        *,
        current_user: User,
        address_data: dict[str, Any],
    ) -> Address:
        data = self._clean_create_data(address_data)

        for field in (
            "address_line_1",
            "city",
            "state",
            "postal_code",
        ):
            value = data.get(field)

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                raise ValidationError(f"{field} is required.")

        requested_default = bool(data.get("is_default", False))

        # These values are controlled by the service.
        data["is_default"] = False
        data["is_active"] = True

        try:
            address = await self.address_repository.create(
                user_id=current_user.id,
                **data,
            )

            if requested_default:
                await self.address_repository.clear_default_for_user(
                    user_id=current_user.id,
                    exclude_address_id=address.id,
                )
                address = await self.address_repository.set_default(address)

            return address

        except ValidationError:
            raise
        except Exception as exc:
            raise ConflictError(
                "Unable to create address."
            ) from exc

    # ============================================================
    # UPDATE
    # ============================================================

    async def update_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
        address_data: dict[str, Any],
    ) -> Address:
        address = await self.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        updates = self._clean_update_data(address_data)

        if not updates:
            return address

        requested_active = updates.get("is_active")
        requested_default = updates.pop("is_default", None)

        # A farm-linked address cannot be deactivated.
        if requested_active is False and address.is_active:
            if await self._is_used_by_farm(address.id):
                raise ConflictError(
                    "This address is used by a farm and cannot be deactivated."
                )

        # An address that is being deactivated cannot remain default.
        if requested_active is False and requested_default is True:
            raise ValidationError(
                "An inactive address cannot be made default."
            )

        if requested_active is False:
            # Service owns this invariant.
            updates["is_default"] = False

        elif requested_default is True:
            # If the address is currently inactive, it cannot become default
            # unless this same request activates it.
            if not address.is_active and requested_active is not True:
                raise ValidationError(
                    "An inactive address cannot be made default."
                )

            try:
                await self.address_repository.clear_default_for_user(
                    user_id=current_user.id,
                    exclude_address_id=address.id,
                )
            except Exception as exc:
                raise ConflictError(
                    "Unable to update default address."
                ) from exc

            updates["is_default"] = True

        elif requested_default is False:
            updates["is_default"] = False

        try:
            updated = await self.address_repository.update(
                address,
                **updates,
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to update address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError("Address not found.")

        return updated

    # ============================================================
    # DEFAULT
    # ============================================================

    async def set_default_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> Address:
        address = await self.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        if not address.is_active:
            raise ValidationError(
                "An inactive address cannot be made default."
            )

        try:
            await self.address_repository.clear_default_for_user(
                user_id=current_user.id,
                exclude_address_id=address.id,
            )
            updated = await self.address_repository.set_default(address)
        except Exception as exc:
            raise ConflictError(
                "Unable to set default address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError("Address not found.")

        return updated

    async def clear_default_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> Address:
        address = await self.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        try:
            updated = await self.address_repository.clear_default(address)
        except Exception as exc:
            raise ConflictError(
                "Unable to clear default address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError("Address not found.")

        return updated

    # ============================================================
    # ACTIVE / INACTIVE
    # ============================================================

    async def deactivate_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> Address:
        address = await self.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        if await self._is_used_by_farm(address.id):
            raise ConflictError(
                "This address is used by a farm and cannot be deactivated."
            )

        try:
            updated = await self.address_repository.deactivate(address)
        except Exception as exc:
            raise ConflictError(
                "Unable to deactivate address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError("Address not found.")

        return updated

    async def activate_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> Address:
        address = await self.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        try:
            updated = await self.address_repository.activate(address)
        except Exception as exc:
            raise ConflictError(
                "Unable to activate address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError("Address not found.")

        return updated

    # ============================================================
    # DELETE
    # ============================================================

    async def delete_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> None:
        address = await self.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        if await self._is_used_by_farm(address.id):
            raise ConflictError(
                "This address is assigned to a farm and cannot be deleted."
            )

        try:
            deleted = await self.address_repository.delete(address)
        except Exception as exc:
            raise ConflictError(
                "Unable to delete address."
            ) from exc

        if not deleted:
            raise ResourceNotFoundError("Address not found.")
