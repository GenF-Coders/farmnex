from __future__ import annotations

from uuid import UUID, uuid4

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
    Business/application service for user addresses.

    Rules:
        - Every address belongs to exactly one user.
        - Clients never provide user_id.
        - Public UUIDs are used by API callers.
        - Default-address changes happen within the same DB
          transaction.
        - Farm-linked addresses cannot be deleted.
    """

    def __init__(
        self,
        *,
        address_repository: AddressRepository,
        farm_repository: FarmRepository | None = None,
    ) -> None:
        self.address_repository = address_repository
        self.farm_repository = farm_repository

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def _clean_create_data(data: dict) -> dict:
        protected_fields = {
            "id",
            "public_id",
            "user_id",
            "created_at",
            "updated_at",
        }

        result = {
            key: value
            for key, value in data.items()
            if key not in protected_fields
        }

        for key, value in result.items():
            if isinstance(value, str):
                result[key] = (
                    value.strip() or None
                )

        return result

    @staticmethod
    def _clean_update_data(data: dict) -> dict:
        protected_fields = {
            "id",
            "public_id",
            "user_id",
            "created_at",
            "updated_at",
        }

        result = {
            key: value
            for key, value in data.items()
            if key not in protected_fields
        }

        for key, value in result.items():
            if isinstance(value, str):
                result[key] = (
                    value.strip() or None
                )

        return result

    # ============================================================
    # READ
    # ============================================================

    async def get_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ) -> Address:
        address = (
            await self.address_repository
            .get_user_address_by_public_id(
                user_id=current_user.id,
                public_id=address_public_id,
            )
        )

        if address is None:
            raise ResourceNotFoundError(
                "Address not found."
            )

        return address

    async def list_addresses(
        self,
        *,
        current_user: User,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Address], int]:
        if offset < 0:
            raise ValidationError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValidationError(
                "Limit must be between 1 and 100."
            )

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

    # ============================================================
    # CREATE
    # ============================================================

    async def create_address(
        self,
        *,
        current_user: User,
        address_data: dict,
    ) -> Address:
        data = self._clean_create_data(
            address_data
        )

        requested_default = bool(
            data.get("is_default", False)
        )

        data["is_default"] = False
        data["is_active"] = True

        try:
            address = await self.address_repository.create(
                public_id=uuid4(),
                user_id=current_user.id,
                **data,
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to create address."
            ) from exc

        if requested_default:
            try:
                await self.address_repository.clear_default_for_user(
                    user_id=current_user.id,
                    exclude_address_id=address.id,
                )

                address = (
                    await self.address_repository.set_default(
                        address
                    )
                )
            except Exception as exc:
                raise ConflictError(
                    "Address was created but could not be "
                    "set as the default address."
                ) from exc

        return address

    # ============================================================
    # UPDATE
    # ============================================================

    async def update_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
        address_data: dict,
    ) -> Address:
        address = await self.get_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        updates = self._clean_update_data(
            address_data
        )

        if not updates:
            return address

        if (
            "is_active" in updates
            and updates["is_active"] is False
            and address.is_active
        ):
            if await self._is_used_by_farm(address.id):
                raise ConflictError(
                    "This address is used by a farm and cannot "
                    "be deactivated."
                )

        requested_default = updates.pop(
            "is_default",
            None,
        )

        if requested_default is True:
            if not address.is_active:
                raise ValidationError(
                    "An inactive address cannot be made default."
                )

            await self.address_repository.clear_default_for_user(
                user_id=current_user.id,
                exclude_address_id=address.id,
            )

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
            raise ResourceNotFoundError(
                "Address not found."
            )

        return updated

    # ============================================================
    # DEFAULT ADDRESS
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

            updated = await self.address_repository.set_default(
                address
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to set default address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError(
                "Address not found."
            )

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
            updated = (
                await self.address_repository.clear_default(
                    address
                )
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to clear default address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError(
                "Address not found."
            )

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
                "This address is used by a farm and cannot "
                "be deactivated."
            )

        try:
            updated = (
                await self.address_repository.deactivate(
                    address
                )
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to deactivate address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError(
                "Address not found."
            )

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
            updated = (
                await self.address_repository.activate(
                    address
                )
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to activate address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError(
                "Address not found."
            )

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
                "This address is assigned to a farm and "
                "cannot be deleted."
            )

        try:
            deleted = await self.address_repository.delete(
                address
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to delete address."
            ) from exc

        if not deleted:
            raise ResourceNotFoundError(
                "Address not found."
            )

    # ============================================================
    # INTERNAL RELATIONSHIP CHECK
    # ============================================================

    async def _is_used_by_farm(
        self,
        address_id: int,
    ) -> bool:
        if self.farm_repository is None:
            return False

        farm = await self.farm_repository.get_by_address_id(
            address_id
        )

        return farm is not None