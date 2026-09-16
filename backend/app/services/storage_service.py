from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.supabase import get_supabase_client


class StorageError(Exception):
    pass


class StorageConfigurationError(StorageError):
    pass


class StorageValidationError(StorageError):
    pass


class StorageProviderError(StorageError):
    pass


class StorageNotFoundError(StorageError):
    pass


@dataclass(frozen=True, slots=True)
class StoredObject:
    object_id: UUID
    bucket: str
    path: str
    content_type: str
    size_bytes: int


class StorageService:
    """Generic async-safe wrapper around server-side Supabase Storage."""

    MAX_BUCKET_LENGTH = 100
    MAX_PATH_LENGTH = 1024
    _BUCKET_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,98}[a-z0-9])?$")

    def __init__(self) -> None:
        self.client = get_supabase_client()

    @classmethod
    def validate_bucket(cls, bucket: str) -> str:
        if not isinstance(bucket, str):
            raise StorageValidationError("Storage bucket must be a string.")
        value = bucket.strip()
        if not value or len(value) > cls.MAX_BUCKET_LENGTH or not cls._BUCKET_PATTERN.fullmatch(value):
            raise StorageValidationError("Invalid storage bucket name.")
        return value

    @classmethod
    def validate_path(cls, path: str) -> str:
        if not isinstance(path, str):
            raise StorageValidationError("Storage path must be a string.")
        value = path.strip()
        if not value or len(value) > cls.MAX_PATH_LENGTH:
            raise StorageValidationError("Invalid storage path.")
        if value.startswith("/") or "\\" in value or "\x00" in value:
            raise StorageValidationError("Invalid storage path.")
        parts = value.split("/")
        if any(not p or p in {".", ".."} for p in parts):
            raise StorageValidationError("Invalid storage path.")
        return value

    @staticmethod
    def validate_file(*, file_bytes: bytes, content_type: str) -> str:
        if not isinstance(file_bytes, bytes) or not file_bytes:
            raise StorageValidationError("The uploaded file is empty.")
        normalized = (content_type or "").strip().lower()
        if not normalized:
            raise StorageValidationError("Uploaded file has no content type.")
        if len(file_bytes) > settings.storage_max_upload_size_bytes:
            limit_mb = settings.storage_max_upload_size_bytes / (1024 * 1024)
            raise StorageValidationError(f"File exceeds the {limit_mb:g} MB upload limit.")
        return normalized

    async def upload(self, *, bucket: str, path: str, file_bytes: bytes, content_type: str, cache_control_seconds: int = 3600) -> StoredObject:
        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)
        content_type = self.validate_file(file_bytes=file_bytes, content_type=content_type)
        options = {"content-type": content_type, "cache-control": str(cache_control_seconds), "upsert": "false"}
        try:
            await asyncio.to_thread(lambda: self.client.storage.from_(bucket).upload(path, file_bytes, file_options=options))
        except Exception as exc:
            raise StorageProviderError("Unable to upload the file to storage.") from exc
        return StoredObject(uuid4(), bucket, path, content_type, len(file_bytes))

    async def replace(self, *, bucket: str, old_path: str, new_path: str, file_bytes: bytes, content_type: str, cache_control_seconds: int = 3600) -> StoredObject:
        bucket = self.validate_bucket(bucket)
        old_path = self.validate_path(old_path)
        new_path = self.validate_path(new_path)
        if old_path == new_path:
            raise StorageValidationError("Replacement object must use a different path.")
        stored = await self.upload(bucket=bucket, path=new_path, file_bytes=file_bytes, content_type=content_type, cache_control_seconds=cache_control_seconds)
        try:
            await self.delete(bucket=bucket, path=old_path)
        except StorageError:
            # The new object is valid; the old object can be cleaned up separately.
            raise
        return stored

    async def download(self, *, bucket: str, path: str) -> bytes:
        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)
        try:
            response = await asyncio.to_thread(lambda: self.client.storage.from_(bucket).download(path))
        except Exception as exc:
            raise StorageProviderError("Unable to download the file from storage.") from exc
        if response is None:
            raise StorageNotFoundError("Storage object was not found.")
        if not isinstance(response, bytes):
            raise StorageProviderError("Storage provider returned invalid file data.")
        return response

    async def create_signed_url(self, *, bucket: str, path: str, expires_in: int | None = None) -> str:
        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)
        ttl = expires_in if expires_in is not None else settings.storage_signed_url_expire_seconds
        if ttl < 60 or ttl > 86400:
            raise StorageValidationError("Signed URL expiry must be between 60 and 86400 seconds.")
        try:
            response = await asyncio.to_thread(lambda: self.client.storage.from_(bucket).create_signed_url(path, ttl))
        except Exception as exc:
            raise StorageProviderError("Unable to create a signed storage URL.") from exc
        if isinstance(response, dict):
            value = response.get("signedURL") or response.get("signedUrl") or response.get("signed_url")
            if value:
                return str(value)
        value = getattr(response, "signed_url", None)
        if value:
            return str(value)
        raise StorageProviderError("Storage provider returned no signed URL.")

    async def get(self, *, bucket: str, path: str, expires_in: int | None = None) -> str:
        return await self.create_signed_url(bucket=bucket, path=path, expires_in=expires_in)

    async def delete(self, *, bucket: str, path: str) -> None:
        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)
        try:
            await asyncio.to_thread(lambda: self.client.storage.from_(bucket).remove([path]))
        except Exception as exc:
            raise StorageProviderError("Unable to delete the file from storage.") from exc

    async def exists(self, *, bucket: str, path: str) -> bool:
        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)
        parent, filename = (path.rsplit("/", 1) if "/" in path else ("", path))
        try:
            response = await asyncio.to_thread(lambda: self.client.storage.from_(bucket).list(parent, {"limit": 1000}))
        except Exception as exc:
            raise StorageProviderError("Unable to check storage object existence.") from exc
        return any(isinstance(item, dict) and item.get("name") == filename for item in (response or []))

    async def list_files(self, *, bucket: str, prefix: str = "", limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        bucket = self.validate_bucket(bucket)
        if not 1 <= limit <= 1000 or offset < 0:
            raise StorageValidationError("Invalid storage list pagination.")
        prefix = prefix.strip("/")
        if prefix:
            prefix = self.validate_path(prefix)
        try:
            response = await asyncio.to_thread(lambda: self.client.storage.from_(bucket).list(prefix, {"limit": limit, "offset": offset, "sortBy": {"column": "name", "order": "asc"}}))
        except Exception as exc:
            raise StorageProviderError("Unable to list storage files.") from exc
        return list(response or [])

    async def health_check(self, *, bucket: str) -> dict[str, Any]:
        bucket = self.validate_bucket(bucket)
        try:
            result = await asyncio.to_thread(lambda: self.client.storage.from_(bucket).list("", {"limit": 1}))
        except Exception as exc:
            raise StorageProviderError("Unable to reach the configured storage bucket.") from exc
        return {"provider": "supabase", "bucket": bucket, "reachable": True, "sample_count": len(result or [])}


storage_service = StorageService()

__all__ = ["StorageError", "StorageConfigurationError", "StorageValidationError", "StorageProviderError", "StorageNotFoundError", "StoredObject", "StorageService", "storage_service"]
