from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.services.storage.exceptions import (
    StorageConfigurationError,
    StorageProviderError,
    StorageValidationError,
)


ALLOWED_IMAGE_CONTENT_TYPES = frozenset({
    "image/jpeg",
    "image/png",
    "image/webp",
})


@dataclass(frozen=True, slots=True)
class StoredObject:
    path: str
    content_type: str
    size_bytes: int


class StorageService:
    """Async-safe application wrapper around server-side Supabase Storage.

    The Supabase Python SDK exposes synchronous storage methods. We execute
    those network calls in worker threads so they do not block FastAPI's
    event loop.
    """

    def __init__(self) -> None:
        self.client = get_supabase_client()
        self.bucket = settings.storage_bucket

    # ------------------------------------------------------------
    # Validation / path handling
    # ------------------------------------------------------------

    @staticmethod
    def validate_image(
        *,
        content_type: str | None,
        size_bytes: int,
    ) -> str:
        normalized_type = (content_type or "").strip().lower()

        if normalized_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise StorageValidationError(
                "Only JPEG, PNG, and WebP images are allowed."
            )

        if size_bytes <= 0:
            raise StorageValidationError("The uploaded file is empty.")

        if size_bytes > settings.storage_max_upload_size_bytes:
            limit_mb = settings.storage_max_upload_size_bytes / (1024 * 1024)
            raise StorageValidationError(
                f"Image exceeds the {limit_mb:g} MB upload limit."
            )

        return normalized_type

    @staticmethod
    def build_user_test_path(user_public_id: UUID, content_type: str) -> str:
        # This endpoint is only for exercising the storage integration.
        # Production profile uploads will use their own namespace later.
        extension = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }.get(content_type)
        if extension is None:
            raise StorageValidationError("Unsupported image type.")
        return f"__storage_tests__/{user_public_id}/{uuid4()}.{extension}"

    @staticmethod
    def build_object_path(*parts: str) -> str:
        cleaned: list[str] = []
        for part in parts:
            value = str(part).strip().strip("/")
            if not value:
                continue
            if ".." in PurePosixPath(value).parts:
                raise StorageValidationError("Invalid storage path.")
            if "\\" in value:
                raise StorageValidationError("Invalid storage path.")
            cleaned.append(value)

        if not cleaned:
            raise StorageValidationError("Storage path cannot be empty.")

        return "/".join(cleaned)

    # ------------------------------------------------------------
    # Provider operations
    # ------------------------------------------------------------

    async def health_check(self) -> dict[str, Any]:
        """Verify that the configured bucket can be reached."""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.storage.from_(self.bucket).list(
                    "",
                    {"limit": 1},
                )
            )
            return {
                "provider": "supabase",
                "bucket": self.bucket,
                "reachable": True,
                "sample_count": len(result or []),
            }
        except Exception as exc:
            raise StorageProviderError(
                "Unable to reach the configured storage bucket."
            ) from exc

    async def upload(
        self,
        *,
        path: str,
        file_bytes: bytes,
        content_type: str,
        cache_control_seconds: int = 3600,
    ) -> StoredObject:
        normalized_type = self.validate_image(
            content_type=content_type,
            size_bytes=len(file_bytes),
        )

        if not file_bytes:
            raise StorageValidationError("The uploaded file is empty.")

        options = {
            "content-type": normalized_type,
            "cache-control": str(cache_control_seconds),
            "upsert": "false",
        }

        try:
            await asyncio.to_thread(
                lambda: self.client.storage.from_(self.bucket).upload(
                    path,
                    file_bytes,
                    file_options=options,
                )
            )
        except Exception as exc:
            raise StorageProviderError(
                "Unable to upload the file to storage."
            ) from exc

        return StoredObject(
            path=path,
            content_type=normalized_type,
            size_bytes=len(file_bytes),
        )

    async def delete(self, *, path: str) -> None:
        try:
            await asyncio.to_thread(
                lambda: self.client.storage.from_(self.bucket).remove([path])
            )
        except Exception as exc:
            raise StorageProviderError(
                "Unable to delete the file from storage."
            ) from exc

    async def create_signed_url(
        self,
        *,
        path: str,
        expires_in: int | None = None,
    ) -> str:
        ttl = expires_in or settings.storage_signed_url_expire_seconds

        if ttl < 60 or ttl > 86400:
            raise StorageValidationError(
                "Signed URL expiry must be between 60 and 86400 seconds."
            )

        try:
            response = await asyncio.to_thread(
                lambda: self.client.storage.from_(self.bucket).create_signed_url(
                    path,
                    ttl,
                )
            )
        except Exception as exc:
            raise StorageProviderError(
                "Unable to create a signed storage URL."
            ) from exc

        if isinstance(response, dict):
            signed_url = response.get("signedURL") or response.get("signedUrl")
            if signed_url:
                return str(signed_url)

        signed_url = getattr(response, "signed_url", None)
        if signed_url:
            return str(signed_url)

        raise StorageProviderError("Storage provider returned no signed URL.")

    async def download(self, *, path: str) -> bytes:
        try:
            response = await asyncio.to_thread(
                lambda: self.client.storage.from_(self.bucket).download(path)
            )
        except Exception as exc:
            raise StorageProviderError(
                "Unable to download the file from storage."
            ) from exc

        if not isinstance(response, bytes):
            raise StorageProviderError("Storage provider returned invalid file data.")

        return response

    async def list_files(
        self,
        *,
        prefix: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        if limit < 1 or limit > 1000:
            raise StorageValidationError("limit must be between 1 and 1000.")
        if offset < 0:
            raise StorageValidationError("offset cannot be negative.")

        try:
            response = await asyncio.to_thread(
                lambda: self.client.storage.from_(self.bucket).list(
                    prefix.strip("/"),
                    {
                        "limit": limit,
                        "offset": offset,
                        "sortBy": {"column": "name", "order": "asc"},
                    },
                )
            )
        except Exception as exc:
            raise StorageProviderError(
                "Unable to list storage files."
            ) from exc

        return list(response or [])


storage_service = StorageService()
