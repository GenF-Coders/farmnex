from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.models.farm import Farm
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.services.exceptions import ConflictError, ForbiddenOperationError, ResourceAlreadyExistsError, ResourceNotFoundError, ValidationError
from app.services.storage_service import StorageError, StorageProviderError, StorageService, StorageValidationError


class FarmService:
    REQUIRED_ROLE = "FARMER"
    FARM_FILE_CONTENT_TYPES = frozenset({"application/pdf", "image/jpeg", "image/png", "image/webp"})
    FARM_FILE_FOLDER = "farm-files"

    def __init__(self, *, farm_repository: FarmRepository, storage_service: StorageService) -> None:
        self.farm_repository = farm_repository
        self.storage_service = storage_service

    def _ensure_farmer(self, *, current_user: User) -> None:
        role = getattr(getattr(current_user, "role", None), "name", None)
        if str(role).upper() != self.REQUIRED_ROLE:
            raise ForbiddenOperationError("Only farmers can manage farms.")

    @staticmethod
    def _clean_data(data: dict[str, Any]) -> dict[str, Any]:
        allowed = {"farm_name", "description", "address_line_1", "address_line_2", "landmark", "village", "city", "district", "state", "postal_code", "country", "latitude", "longitude", "is_active"}
        return {k: (v.strip() or None if isinstance(v, str) else v) for k, v in data.items() if k in allowed}

    @staticmethod
    def _storage_bucket() -> str:
        bucket = settings.storage_bucket
        if not isinstance(bucket, str) or not bucket.strip():
            raise ConflictError("Storage bucket is not configured.")
        return bucket.strip()

    @classmethod
    def _build_farm_file_path(cls, *, content_type: str) -> str:
        ext = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}.get(content_type)
        if not ext:
            raise ValidationError("Only PDF, JPEG, PNG, and WebP farm files are allowed.")
        return f"{cls.FARM_FILE_FOLDER}/{uuid4()}.{ext}"

    @classmethod
    def _validate_stored_path(cls, path: str) -> None:
        parts = path.split("/")
        if len(parts) != 2 or parts[0] != cls.FARM_FILE_FOLDER or not parts[1]:
            raise ConflictError("Farm file storage reference is invalid.")

    def _validate_file(self, *, file_bytes: bytes, content_type: str) -> str:
        normalized = (content_type or "").strip().lower()
        if normalized not in self.FARM_FILE_CONTENT_TYPES:
            raise ValidationError("Only PDF, JPEG, PNG, and WebP farm files are allowed.")
        try:
            return self.storage_service.validate_file(file_bytes=file_bytes, content_type=normalized)
        except StorageValidationError as exc:
            raise ValidationError(str(exc)) from exc

    async def get_farm(self, *, current_user: User, farm_public_id: UUID) -> Farm:
        self._ensure_farmer(current_user=current_user)
        farm = await self.farm_repository.get_user_farm_by_public_id(user_id=current_user.id, public_id=farm_public_id)
        if farm is None:
            raise ResourceNotFoundError("Farm not found.")
        return farm

    async def list_farms(self, *, current_user: User, offset: int = 0, limit: int = 20) -> tuple[list[Farm], int]:
        self._ensure_farmer(current_user=current_user)
        return await self.farm_repository.list_by_user_id(user_id=current_user.id, offset=offset, limit=limit), await self.farm_repository.count_by_user_id(current_user.id)

    async def create_farm(self, *, current_user: User, farm_data: dict[str, Any]) -> Farm:
        self._ensure_farmer(current_user=current_user)
        data = self._clean_data(farm_data)
        if not data.get("farm_name"):
            raise ValidationError("Farm name is required.")
        if await self.farm_repository.get_user_farm_by_name(user_id=current_user.id, farm_name=data["farm_name"]):
            raise ResourceAlreadyExistsError("You already have a farm with this name.")
        try:
            return await self.farm_repository.create(public_id=uuid4(), user_id=current_user.id, **data)
        except Exception as exc:
            raise ConflictError("Unable to create farm.") from exc

    async def update_farm(self, *, current_user: User, farm_public_id: UUID, farm_data: dict[str, Any]) -> Farm:
        farm = await self.get_farm(current_user=current_user, farm_public_id=farm_public_id)
        updates = self._clean_data(farm_data)
        if "farm_name" in updates:
            if not updates["farm_name"]:
                raise ValidationError("Farm name cannot be empty.")
            existing = await self.farm_repository.get_user_farm_by_name(user_id=current_user.id, farm_name=updates["farm_name"])
            if existing and existing.id != farm.id:
                raise ResourceAlreadyExistsError("You already have a farm with this name.")
        return await self.farm_repository.update(farm, **updates) if updates else farm

    async def upload_farm_file(self, *, current_user: User, farm_public_id: UUID, file_bytes: bytes, content_type: str) -> Farm:
        farm = await self.get_farm(current_user=current_user, farm_public_id=farm_public_id)
        normalized = self._validate_file(file_bytes=file_bytes, content_type=content_type)
        new_path = self._build_farm_file_path(content_type=normalized)
        bucket = self._storage_bucket()
        old_path = farm.farm_file_path
        try:
            await self.storage_service.upload(bucket=bucket, path=new_path, file_bytes=file_bytes, content_type=normalized)
            updated = await self.farm_repository.update_file(farm, file_path=new_path, content_type=normalized)
        except StorageValidationError as exc:
            raise ValidationError(str(exc)) from exc
        except StorageProviderError as exc:
            raise ConflictError("Unable to upload farm file.") from exc
        except StorageError as exc:
            raise ConflictError("Farm file upload failed.") from exc
        except Exception:
            try: await self.storage_service.delete(bucket=bucket, path=new_path)
            except StorageError: pass
            raise
        if updated is None:
            raise ResourceNotFoundError("Farm not found.")
        if old_path:
            try: await self.storage_service.delete(bucket=bucket, path=old_path)
            except StorageError: pass
        return updated

    async def replace_farm_file(self, *, current_user: User, farm_public_id: UUID, file_bytes: bytes, content_type: str) -> Farm:
        return await self.upload_farm_file(current_user=current_user, farm_public_id=farm_public_id, file_bytes=file_bytes, content_type=content_type)

    async def get_farm_file_url(self, *, current_user: User, farm_public_id: UUID) -> tuple[Farm, str, int]:
        farm = await self.get_farm(current_user=current_user, farm_public_id=farm_public_id)
        if not farm.farm_file_path or not farm.farm_file_content_type:
            raise ResourceNotFoundError("Farm file not found.")
        self._validate_stored_path(farm.farm_file_path)
        expires = settings.storage_signed_url_expire_seconds
        try:
            url = await self.storage_service.create_signed_url(bucket=self._storage_bucket(), path=farm.farm_file_path, expires_in=expires)
        except StorageProviderError as exc:
            raise ConflictError("Unable to generate farm file URL.") from exc
        except StorageError as exc:
            raise ConflictError("Unable to access farm file.") from exc
        return farm, url, expires

    async def download_farm_file(self, *, current_user: User, farm_public_id: UUID) -> tuple[Farm, bytes, str]:
        farm = await self.get_farm(current_user=current_user, farm_public_id=farm_public_id)
        if not farm.farm_file_path or not farm.farm_file_content_type:
            raise ResourceNotFoundError("Farm file not found.")
        self._validate_stored_path(farm.farm_file_path)
        try:
            data = await self.storage_service.download(bucket=self._storage_bucket(), path=farm.farm_file_path)
        except StorageProviderError as exc:
            raise ConflictError("Unable to download farm file.") from exc
        except StorageError as exc:
            raise ConflictError("Farm file download failed.") from exc
        return farm, data, farm.farm_file_content_type

    async def delete_farm_file(self, *, current_user: User, farm_public_id: UUID) -> None:
        farm = await self.get_farm(current_user=current_user, farm_public_id=farm_public_id)
        if not farm.farm_file_path:
            raise ResourceNotFoundError("Farm file not found.")
        path = farm.farm_file_path
        self._validate_stored_path(path)
        updated = await self.farm_repository.clear_file(farm)
        if updated is None:
            raise ResourceNotFoundError("Farm not found.")
        try: await self.storage_service.delete(bucket=self._storage_bucket(), path=path)
        except StorageError as exc: raise ConflictError("Farm file reference was removed, but the storage object could not be deleted.") from exc

    async def delete_farm(self, *, current_user: User, farm_public_id: UUID) -> None:
        farm = await self.get_farm(current_user=current_user, farm_public_id=farm_public_id)
        path = farm.farm_file_path
        if path: self._validate_stored_path(path)
        if not await self.farm_repository.delete(farm):
            raise ResourceNotFoundError("Farm not found.")
        if path:
            try: await self.storage_service.delete(bucket=self._storage_bucket(), path=path)
            except StorageError: pass
