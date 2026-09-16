from __future__ import annotations

from typing import Any
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.models.farm import Farm
from app.repositories.farm_repository import FarmRepository
from app.services.storage_service import (
    StorageError,
    storage_service,
)


class FarmService:
    """
    Business/application service for Farm.

    Storage:
        storage-bucket/
            farm-files/
                <uuid>.<extension>

    Database stores only the permanent storage path.
    Signed URLs are generated dynamically.
    """

    FARM_FILE_FOLDER = "farm-files"

    def __init__(
        self,
        repository: FarmRepository,
    ) -> None:
        self.repository = repository
        self.storage_service = storage_service

    # ================================================================
    # VALIDATION HELPERS
    # ================================================================

    @staticmethod
    def _normalize_farm_name(
        farm_name: str | None,
    ) -> str:
        if farm_name is None:
            raise ValidationError(
                "Farm name is required."
            )

        normalized = farm_name.strip()

        if not normalized:
            raise ValidationError(
                "Farm name is required."
            )

        return normalized

    # ================================================================
    # CREATE
    # ================================================================

    async def create_farm(
        self,
        *,
        user_id: int,
        farm_data: dict[str, Any],
    ) -> Farm:
        data = dict(farm_data)

        farm_name = self._normalize_farm_name(
            data.get("farm_name")
        )

        data["farm_name"] = farm_name
        data["user_id"] = user_id

        # Never allow API data to control protected fields.
        protected_fields = {
            "id",
            "public_id",
            "user_id",
            "created_at",
            "updated_at",
            "farm_file_path",
            "farm_file_content_type",
        }

        data = {
            key: value
            for key, value in data.items()
            if key not in protected_fields
        }

        if await self.repository.exists_for_user(
            user_id=user_id,
            farm_name=farm_name,
        ):
            raise ConflictError(
                f"A farm named '{farm_name}' already exists."
            )

        try:
            return await self.repository.create(
                user_id=user_id,
                **data,
            )
        except Exception as exc:
            # The DB unique index is the final protection
            # against concurrent duplicate creation.
            raise ConflictError(
                f"Unable to create farm '{farm_name}'."
            ) from exc

    # ================================================================
    # READ
    # ================================================================

    async def get_farm(
        self,
        *,
        user_id: int,
        farm_public_id: UUID,
    ) -> Farm:
        farm = await self.repository.get_user_farm_by_public_id(
            user_id=user_id,
            public_id=farm_public_id,
        )

        if farm is None:
            raise NotFoundError(
                "Farm not found."
            )

        return farm

    async def list_farms(
        self,
        *,
        user_id: int,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Farm], int]:
        if offset < 0:
            raise ValidationError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValidationError(
                "Limit must be between 1 and 100."
            )

        farms = await self.repository.list_by_user_id(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )

        total = await self.repository.count_by_user_id(
            user_id=user_id,
        )

        return farms, total

    # ================================================================
    # UPDATE
    # ================================================================

    async def update_farm(
        self,
        *,
        user_id: int,
        farm_public_id: UUID,
        farm_data: dict[str, Any],
    ) -> Farm:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        data = dict(farm_data)

        # Never allow protected fields to be updated.
        protected_fields = {
            "id",
            "public_id",
            "user_id",
            "created_at",
            "updated_at",
            "farm_file_path",
            "farm_file_content_type",
        }

        data = {
            key: value
            for key, value in data.items()
            if key not in protected_fields
        }

        if "farm_name" in data:
            farm_name = self._normalize_farm_name(
                data["farm_name"]
            )

            if await self.repository.exists_for_user(
                user_id=user_id,
                farm_name=farm_name,
                exclude_id=farm.id,
            ):
                raise ConflictError(
                    f"A farm named '{farm_name}' already exists."
                )

            data["farm_name"] = farm_name

        updated_farm = await self.repository.update(
            farm,
            **data,
        )

        if updated_farm is None:
            raise NotFoundError(
                "Farm not found."
            )

        return updated_farm

    # ================================================================
    # DELETE
    # ================================================================

    async def delete_farm(
        self,
        *,
        user_id: int,
        farm_public_id: UUID,
    ) -> None:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        old_path = farm.farm_file_path

        await self.repository.delete(farm)

        # DB deletion has succeeded.
        # Storage cleanup is intentionally best effort.
        if old_path:
            try:
                self._validate_stored_path(
                    old_path
                )

                await self.storage_service.delete(
                    bucket=settings.storage_bucket,
                    path=old_path,
                )
            except Exception:
                pass

    # ================================================================
    # FARM FILE HELPERS
    # ================================================================

    def _build_farm_file_path(
        self,
        content_type: str,
    ) -> str:
        return self.storage_service.build_uuid_path(
            folder=self.FARM_FILE_FOLDER,
            content_type=content_type,
        )

    def _validate_file(
        self,
        *,
        file_bytes: bytes,
        content_type: str,
    ) -> None:
        self.storage_service.validate_file(
            file_bytes=file_bytes,
            content_type=content_type,
            verify_signature=True,
        )

    def _validate_stored_path(
        self,
        path: str,
    ) -> None:
        validated_path = (
            self.storage_service.validate_managed_path(
                path
            )
        )

        if not validated_path.startswith(
            f"{self.FARM_FILE_FOLDER}/"
        ):
            raise ValidationError(
                "Invalid farm file storage path."
            )

    # ================================================================
    # UPLOAD / REPLACE FARM FILE
    # ================================================================

    async def upload_farm_file(
        self,
        *,
        user_id: int,
        farm_public_id: UUID,
        file_bytes: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> tuple[str, str]:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        if not file_bytes:
            raise ValidationError(
                "Farm file cannot be empty."
            )

        normalized_content_type = (
            self.storage_service.normalize_content_type(
                content_type
            )
        )

        self._validate_file(
            file_bytes=file_bytes,
            content_type=normalized_content_type,
        )

        bucket = settings.storage_bucket

        new_path = self._build_farm_file_path(
            normalized_content_type
        )

        old_path = farm.farm_file_path

        # ------------------------------------------------------------
        # Upload new file first.
        # ------------------------------------------------------------

        await self.storage_service.upload(
            bucket=bucket,
            path=new_path,
            file_bytes=file_bytes,
            content_type=normalized_content_type,
        )

        try:
            # StorageService returns ONLY the signed URL.
            signed_url = (
                await self.storage_service.create_signed_url(
                    bucket=bucket,
                    path=new_path,
                )
            )

            # DB stores ONLY permanent storage path.
            updated_farm = (
                await self.repository.update_file(
                    farm,
                    file_path=new_path,
                    content_type=normalized_content_type,
                )
            )

            if updated_farm is None:
                raise RuntimeError(
                    "Failed to update farm file metadata."
                )

        except Exception:
            # Remove newly uploaded object if DB update
            # or signed URL generation fails.
            try:
                await self.storage_service.delete(
                    bucket=bucket,
                    path=new_path,
                )
            except Exception:
                pass

            raise

        # ------------------------------------------------------------
        # Delete old file only after DB has been updated.
        # ------------------------------------------------------------

        if old_path and old_path != new_path:
            try:
                self._validate_stored_path(
                    old_path
                )

                await self.storage_service.delete(
                    bucket=bucket,
                    path=old_path,
                )
            except Exception:
                # Old-file cleanup must not make a successful
                # replacement fail.
                pass

        return (
            signed_url,
            normalized_content_type,
        )

    # ================================================================
    # GET FARM FILE URL
    # ================================================================

    async def get_farm_file_url(
        self,
        *,
        user_id: int,
        farm_public_id: UUID,
    ) -> tuple[str, str | None]:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        if not farm.farm_file_path:
            raise NotFoundError(
                "Farm does not have a file."
            )

        self._validate_stored_path(
            farm.farm_file_path
        )

        signed_url = (
            await self.storage_service.create_signed_url(
                bucket=settings.storage_bucket,
                path=farm.farm_file_path,
            )
        )

        return (
            signed_url,
            farm.farm_file_content_type,
        )

    # ================================================================
    # DOWNLOAD FARM FILE
    # ================================================================

    async def download_farm_file(
        self,
        *,
        user_id: int,
        farm_public_id: UUID,
    ) -> tuple[bytes, str]:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        if not farm.farm_file_path:
            raise NotFoundError(
                "Farm does not have a file."
            )

        self._validate_stored_path(
            farm.farm_file_path
        )

        file_bytes = (
            await self.storage_service.download(
                bucket=settings.storage_bucket,
                path=farm.farm_file_path,
            )
        )

        return (
            file_bytes,
            farm.farm_file_content_type
            or "application/octet-stream",
        )

    # ================================================================
    # DELETE FARM FILE
    # ================================================================

    async def delete_farm_file(
        self,
        *,
        user_id: int,
        farm_public_id: UUID,
    ) -> None:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        if not farm.farm_file_path:
            raise NotFoundError(
                "Farm does not have a file."
            )

        old_path = farm.farm_file_path

        # Clear DB first.
        updated_farm = (
            await self.repository.clear_file(farm)
        )

        if updated_farm is None:
            raise NotFoundError(
                "Farm not found."
            )

        # Storage cleanup is best effort.
        try:
            self._validate_stored_path(
                old_path
            )

            await self.storage_service.delete(
                bucket=settings.storage_bucket,
                path=old_path,
            )
        except Exception:
            pass

    # ================================================================
    # RESPONSE
    # ================================================================

    async def build_farm_response_data(
        self,
        farm: Farm,
    ) -> dict[str, Any]:
        data = {
            "public_id": str(
                farm.public_id
            ),
            "farm_name": farm.farm_name,
            "description": farm.description,

            "address_line_1": farm.address_line_1,
            "address_line_2": farm.address_line_2,
            "landmark": farm.landmark,
            "village": farm.village,
            "city": farm.city,
            "district": farm.district,
            "state": farm.state,
            "postal_code": farm.postal_code,
            "country": farm.country,
            "latitude": farm.latitude,
            "longitude": farm.longitude,

            "is_active": farm.is_active,

            "farm_file_url": None,
            "farm_file_content_type": (
                farm.farm_file_content_type
            ),

            "created_at": farm.created_at,
            "updated_at": farm.updated_at,
        }

        if farm.farm_file_path:
            try:
                self._validate_stored_path(
                    farm.farm_file_path
                )

                signed_url = (
                    await self.storage_service.create_signed_url(
                        bucket=settings.storage_bucket,
                        path=farm.farm_file_path,
                    )
                )

                data["farm_file_url"] = signed_url

            except Exception:
                # Never expose internal storage paths.
                data["farm_file_url"] = None

        return data