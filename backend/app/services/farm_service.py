from __future__ import annotations

from uuid import UUID, uuid4

from app.models.farm import Farm
from app.models.user import User
from app.repositories.address_repository import AddressRepository
from app.repositories.farm_repository import FarmRepository
from app.services.exceptions import (
    ConflictError,
    ForbiddenOperationError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)


class FarmService:
    """
    Business/application service for farms.

    Critical security rule:

        A farmer may only assign an address that belongs to
        the same authenticated user.

    Database integer IDs are never accepted from the API.
    """

    REQUIRED_ROLE = "FARMER"

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        address_repository: AddressRepository,
    ) -> None:
        self.farm_repository = farm_repository
        self.address_repository = address_repository

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
            "address_id",
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
            "address_id",
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

    def _ensure_farmer(
        self,
        *,
        current_user: User,
    ) -> None:
        role = getattr(
            getattr(current_user, "role", None),
            "name",
            None,
        )

        if role is None:
            raise ForbiddenOperationError(
                "Farmer role information is unavailable."
            )

        if str(role).upper() != self.REQUIRED_ROLE:
            raise ForbiddenOperationError(
                "Only farmers can manage farms."
            )

    # ============================================================
    # ADDRESS OWNERSHIP
    # ============================================================

    async def _get_owned_address(
        self,
        *,
        current_user: User,
        address_public_id: UUID,
    ):
        address = (
            await self.address_repository
            .get_user_address_by_public_id(
                user_id=current_user.id,
                public_id=address_public_id,
            )
        )

        if address is None:
            # Do not reveal whether the address belongs to another
            # user. Treat it as unavailable to this caller.
            raise ResourceNotFoundError(
                "Address not found."
            )

        if not address.is_active:
            raise ValidationError(
                "The selected address is inactive."
            )

        return address

    # ============================================================
    # READ
    # ============================================================

    async def get_farm(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
    ) -> Farm:
        self._ensure_farmer(
            current_user=current_user
        )

        farm = (
            await self.farm_repository
            .get_user_farm_by_public_id(
                user_id=current_user.id,
                public_id=farm_public_id,
            )
        )

        if farm is None:
            raise ResourceNotFoundError(
                "Farm not found."
            )

        return farm

    async def list_farms(
        self,
        *,
        current_user: User,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Farm], int]:
        self._ensure_farmer(
            current_user=current_user
        )

        if offset < 0:
            raise ValidationError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValidationError(
                "Limit must be between 1 and 100."
            )

        farms = await self.farm_repository.list_by_user_id(
            user_id=current_user.id,
            offset=offset,
            limit=limit,
        )

        total = await self.farm_repository.count_by_user_id(
            user_id=current_user.id,
        )

        return farms, total

    # ============================================================
    # CREATE
    # ============================================================

    async def create_farm(
        self,
        *,
        current_user: User,
        farm_data: dict,
    ) -> Farm:
        self._ensure_farmer(
            current_user=current_user
        )

        data = dict(farm_data)

        address_public_id = data.pop(
            "address_public_id",
            None,
        )

        if address_public_id is None:
            raise ValidationError(
                "Farm address is required."
            )

        address = await self._get_owned_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        clean_data = self._clean_create_data(
            data
        )

        farm_name = clean_data.get("farm_name")

        if not farm_name:
            raise ValidationError(
                "Farm name is required."
            )

        # This is intentionally an ownership-scoped check.
        existing = await self.farm_repository.get_user_farm(
            user_id=current_user.id,
            farm_name=farm_name,
        )

        if existing is not None:
            raise ResourceAlreadyExistsError(
                "You already have a farm with this name."
            )

        try:
            farm = await self.farm_repository.create(
                public_id=uuid4(),
                user_id=current_user.id,
                address_id=address.id,
                **clean_data,
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to create farm."
            ) from exc

        return farm

    # ============================================================
    # UPDATE
    # ============================================================

    async def update_farm(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
        farm_data: dict,
    ) -> Farm:
        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        data = dict(farm_data)

        address_public_id = data.pop(
            "address_public_id",
            None,
        )

        updates = self._clean_update_data(
            data
        )

        if "farm_name" in updates:
            farm_name = updates["farm_name"]

            if not farm_name:
                raise ValidationError(
                    "Farm name cannot be empty."
                )

            existing = await self.farm_repository.get_user_farm(
                user_id=current_user.id,
                farm_name=farm_name,
            )

            if (
                existing is not None
                and existing.id != farm.id
            ):
                raise ResourceAlreadyExistsError(
                    "You already have a farm with this name."
                )

        if updates:
            try:
                updated_farm = (
                    await self.farm_repository.update(
                        farm,
                        **updates,
                    )
                )
            except Exception as exc:
                raise ConflictError(
                    "Unable to update farm."
                ) from exc

            if updated_farm is None:
                raise ResourceNotFoundError(
                    "Farm not found."
                )

            farm = updated_farm

        # Address is updated separately because the service must
        # validate ownership before touching farm.address_id.
        if address_public_id is not None:
            address = await self._get_owned_address(
                current_user=current_user,
                address_public_id=address_public_id,
            )

            if address.id != farm.address_id:
                try:
                    updated_farm = (
                        await self.farm_repository.update_address(
                            farm,
                            address.id,
                        )
                    )
                except Exception as exc:
                    raise ConflictError(
                        "Unable to change farm address."
                    ) from exc

                if updated_farm is None:
                    raise ResourceNotFoundError(
                        "Farm not found."
                    )

                farm = updated_farm

        return farm

    # ============================================================
    # CHANGE ADDRESS
    # ============================================================

    async def change_farm_address(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
        address_public_id: UUID,
    ) -> Farm:
        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        address = await self._get_owned_address(
            current_user=current_user,
            address_public_id=address_public_id,
        )

        if farm.address_id == address.id:
            return farm

        try:
            updated = (
                await self.farm_repository.update_address(
                    farm,
                    address.id,
                )
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to change farm address."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError(
                "Farm not found."
            )

        return updated

    # ============================================================
    # DELETE
    # ============================================================

    async def delete_farm(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
    ) -> None:
        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        try:
            deleted = await self.farm_repository.delete(
                farm
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to delete farm."
            ) from exc

        if not deleted:
            raise ResourceNotFoundError(
                "Farm not found."
            )