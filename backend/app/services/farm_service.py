from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.models.farm import Farm
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.services.exceptions import (
    ConflictError,
    ForbiddenOperationError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.storage_service import (
    StorageError,
    StorageProviderError,
    StorageService,
    StorageValidationError,
)


class FarmService:
    """
    Business/application service for farms.

    Responsibilities:
        - farmer authorization
        - farm ownership
        - farm validation
        - farm address management
        - farm file lifecycle
        - storage ownership/path rules

    Transaction rule:
        This service does not commit or rollback.

        The database transaction boundary owns commits
        and rollbacks.

    Storage rule:
        FarmService owns farm-specific storage rules.

        StorageService owns generic storage infrastructure.
    """

    REQUIRED_ROLE = "FARMER"

    FARM_FILE_CONTENT_TYPES = frozenset(
        {
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/pdf",
        }
    )

    FARM_STORAGE_PREFIX = "users"

    # ============================================================
    # CONSTRUCTOR
    # ============================================================

    def __init__(
        self,
        *,
        farm_repository: FarmRepository,
        storage_service: StorageService,
    ) -> None:
        self.farm_repository = farm_repository
        self.storage_service = storage_service

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _storage_bucket() -> str:
        bucket = settings.storage_bucket

        if (
            not isinstance(bucket, str)
            or not bucket.strip()
        ):
            raise ConflictError(
                "Storage bucket is not configured."
            )

        return bucket.strip()

    @staticmethod
    def _normalize_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    def _ensure_farmer(
        self,
        *,
        current_user: User,
    ) -> None:
        role = getattr(
            getattr(
                current_user,
                "role",
                None,
            ),
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

    @classmethod
    def _farm_file_prefix(
        cls,
        user_public_id: UUID,
        farm_public_id: UUID,
    ) -> str:
        return (
            f"{cls.FARM_STORAGE_PREFIX}/"
            f"{user_public_id}/"
            f"farm/"
            f"{farm_public_id}/"
        )

    @classmethod
    def _farm_file_path(
        cls,
        *,
        user_public_id: UUID,
        farm_public_id: UUID,
        content_type: str,
    ) -> str:
        extension_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "application/pdf": "pdf",
        }

        extension = extension_map.get(
            content_type.strip().lower()
        )

        if extension is None:
            raise ValidationError(
                "Unsupported farm file type."
            )

        prefix = cls._farm_file_prefix(
            user_public_id=user_public_id,
            farm_public_id=farm_public_id,
        )

        return f"{prefix}{uuid4()}.{extension}"

    @classmethod
    def _validate_farm_file_path(
        cls,
        *,
        user_public_id: UUID,
        farm_public_id: UUID,
        path: str,
    ) -> None:
        expected_prefix = cls._farm_file_prefix(
            user_public_id=user_public_id,
            farm_public_id=farm_public_id,
        )

        if not path.startswith(expected_prefix):
            raise ConflictError(
                "Farm file storage reference is invalid."
            )

    @staticmethod
    def _clean_create_data(
        data: dict[str, Any],
    ) -> dict[str, Any]:
        allowed_fields = {
            "farm_name",
            "description",
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
            "farm_name",
            "description",
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
        }

        result: dict[str, Any] = {}

        for key, value in data.items():
            if key not in allowed_fields:
                continue

            if isinstance(value, str):
                value = value.strip() or None

            result[key] = value

        return result

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
            current_user=current_user,
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
            current_user=current_user,
        )

        if offset < 0:
            raise ValidationError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValidationError(
                "Limit must be between 1 and 100."
            )

        items = (
            await self.farm_repository
            .list_by_user_id(
                user_id=current_user.id,
                offset=offset,
                limit=limit,
            )
        )

        total = (
            await self.farm_repository
            .count_by_user_id(
                user_id=current_user.id,
            )
        )

        return items, total

    # ============================================================
    # CREATE
    # ============================================================

    async def create_farm(
        self,
        *,
        current_user: User,
        farm_data: dict[str, Any],
    ) -> Farm:
        self._ensure_farmer(
            current_user=current_user,
        )

        clean_data = self._clean_create_data(
            farm_data
        )

        required_fields = (
            "farm_name",
            "address_line_1",
            "city",
            "state",
            "postal_code",
        )

        for field in required_fields:
            value = clean_data.get(field)

            if value is None or (
                isinstance(value, str)
                and not value.strip()
            ):
                raise ValidationError(
                    f"{field} is required."
                )

        existing = (
            await self.farm_repository
            .get_user_farm(
                user_id=current_user.id,
                farm_name=clean_data["farm_name"],
            )
        )

        if existing is not None:
            raise ResourceAlreadyExistsError(
                "You already have a farm with this name."
            )

        try:
            farm = await self.farm_repository.create(
                public_id=uuid4(),
                user_id=current_user.id,
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
        farm_data: dict[str, Any],
    ) -> Farm:
        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        updates = self._clean_update_data(
            farm_data
        )

        if not updates:
            return farm

        if "farm_name" in updates:
            farm_name = updates["farm_name"]

            if not farm_name:
                raise ValidationError(
                    "Farm name cannot be empty."
                )

            existing = (
                await self.farm_repository
                .get_user_farm(
                    user_id=current_user.id,
                    farm_name=farm_name,
                )
            )

            if (
                existing is not None
                and existing.id != farm.id
            ):
                raise ResourceAlreadyExistsError(
                    "You already have a farm with this name."
                )

        required_address_fields = (
            "address_line_1",
            "city",
            "state",
            "postal_code",
        )

        for field in required_address_fields:
            if field not in updates:
                continue

            value = updates[field]

            if value is None or (
                isinstance(value, str)
                and not value.strip()
            ):
                raise ValidationError(
                    f"{field} cannot be empty."
                )

        try:
            updated = (
                await self.farm_repository.update(
                    farm,
                    **updates,
                )
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to update farm."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError(
                "Farm not found."
            )

        return updated

    # ============================================================
    # FARM FILE - UPLOAD / REPLACE
    # ============================================================

    async def upload_farm_file(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
        file_bytes: bytes,
        content_type: str,
    ) -> tuple[Farm, str]:
        self._ensure_farmer(
            current_user=current_user,
        )

        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        normalized_content_type = (
            content_type or ""
        ).strip().lower()

        if (
            normalized_content_type
            not in self.FARM_FILE_CONTENT_TYPES
        ):
            raise ValidationError(
                "Only JPEG, PNG, WebP, and PDF farm files "
                "are allowed."
            )

        try:
            normalized_content_type = (
                self.storage_service.validate_file(
                    file_bytes=file_bytes,
                    content_type=normalized_content_type,
                )
            )
        except StorageValidationError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        new_path = self._farm_file_path(
            user_public_id=current_user.public_id,
            farm_public_id=farm.public_id,
            content_type=normalized_content_type,
        )

        old_path = farm.farm_file_path

        try:
            await self.storage_service.upload(
                bucket=self._storage_bucket(),
                path=new_path,
                file_bytes=file_bytes,
                content_type=normalized_content_type,
            )
        except StorageValidationError as exc:
            raise ValidationError(
                str(exc)
            ) from exc
        except StorageProviderError as exc:
            raise ConflictError(
                "Unable to upload farm file."
            ) from exc
        except StorageError as exc:
            raise ConflictError(
                "Farm file upload failed."
            ) from exc

        try:
            updated_farm = (
                await self.farm_repository.update_file(
                    farm,
                    farm_file_path=new_path,
                    farm_file_content_type=(
                        normalized_content_type
                    ),
                )
            )

            if updated_farm is None:
                raise ResourceNotFoundError(
                    "Farm not found."
                )

        except Exception:
            try:
                await self.storage_service.delete(
                    bucket=self._storage_bucket(),
                    path=new_path,
                )
            except StorageError:
                pass

            raise

        if old_path and old_path != new_path:
            try:
                self._validate_farm_file_path(
                    user_public_id=current_user.public_id,
                    farm_public_id=farm.public_id,
                    path=old_path,
                )

                await self.storage_service.delete(
                    bucket=self._storage_bucket(),
                    path=old_path,
                )
            except StorageError:
                pass
            except ConflictError:
                pass

        try:
            file_url = (
                await self.storage_service
                .create_signed_url(
                    bucket=self._storage_bucket(),
                    path=new_path,
                    expires_in=(
                        settings
                        .storage_signed_url_expire_seconds
                    ),
                )
            )
        except StorageProviderError as exc:
            raise ConflictError(
                "Unable to generate farm file URL."
            ) from exc
        except StorageError as exc:
            raise ConflictError(
                "Unable to access farm file."
            ) from exc

        return updated_farm, file_url

    # ============================================================
    # FARM FILE - GET SIGNED URL
    # ============================================================

    async def get_farm_file_url(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
    ) -> str:
        self._ensure_farmer(
            current_user=current_user,
        )

        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        path = farm.farm_file_path

        if not path:
            raise ResourceNotFoundError(
                "Farm file not found."
            )

        self._validate_farm_file_path(
            user_public_id=current_user.public_id,
            farm_public_id=farm.public_id,
            path=path,
        )

        try:
            return (
                await self.storage_service
                .create_signed_url(
                    bucket=self._storage_bucket(),
                    path=path,
                    expires_in=(
                        settings
                        .storage_signed_url_expire_seconds
                    ),
                )
            )
        except StorageProviderError as exc:
            raise ConflictError(
                "Unable to generate farm file URL."
            ) from exc
        except StorageError as exc:
            raise ConflictError(
                "Unable to access farm file."
            ) from exc

    # ============================================================
    # FARM FILE - DOWNLOAD
    # ============================================================

    async def download_farm_file(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
    ) -> tuple[bytes, str]:
        self._ensure_farmer(
            current_user=current_user,
        )

        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        path = farm.farm_file_path
        content_type = farm.farm_file_content_type

        if not path:
            raise ResourceNotFoundError(
                "Farm file not found."
            )

        if not content_type:
            raise ConflictError(
                "Farm file content type is missing."
            )

        self._validate_farm_file_path(
            user_public_id=current_user.public_id,
            farm_public_id=farm.public_id,
            path=path,
        )

        try:
            file_bytes = (
                await self.storage_service.download(
                    bucket=self._storage_bucket(),
                    path=path,
                )
            )
        except StorageProviderError as exc:
            raise ConflictError(
                "Unable to download farm file."
            ) from exc
        except StorageError as exc:
            raise ConflictError(
                "Farm file download failed."
            ) from exc

        return file_bytes, content_type

    # ============================================================
    # FARM FILE - DELETE
    # ============================================================

    async def delete_farm_file(
        self,
        *,
        current_user: User,
        farm_public_id: UUID,
    ) -> None:
        self._ensure_farmer(
            current_user=current_user,
        )

        farm = await self.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        path = farm.farm_file_path

        if not path:
            raise ResourceNotFoundError(
                "Farm file not found."
            )

        self._validate_farm_file_path(
            user_public_id=current_user.public_id,
            farm_public_id=farm.public_id,
            path=path,
        )

        updated_farm = (
            await self.farm_repository.clear_file(
                farm
            )
        )

        if updated_farm is None:
            raise ResourceNotFoundError(
                "Farm not found."
            )

        try:
            await self.storage_service.delete(
                bucket=self._storage_bucket(),
                path=path,
            )
        except StorageError as exc:
            raise ConflictError(
                "Farm file reference was removed, but the "
                "storage object could not be deleted."
            ) from exc

    # ============================================================
    # DELETE FARM
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

        file_path = farm.farm_file_path

        if file_path:
            self._validate_farm_file_path(
                user_public_id=current_user.public_id,
                farm_public_id=farm.public_id,
                path=file_path,
            )

        try:
            deleted = (
                await self.farm_repository.delete(
                    farm
                )
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to delete farm."
            ) from exc

        if not deleted:
            raise ResourceNotFoundError(
                "Farm not found."
            )

        if file_path:
            try:
                await self.storage_service.delete(
                    bucket=self._storage_bucket(),
                    path=file_path,
                )
            except StorageError as exc:
                raise ConflictError(
                    "Farm was deleted, but its storage file "
                    "could not be deleted."
                ) from exc