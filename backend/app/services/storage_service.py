from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.supabase import get_supabase_client


# ============================================================
# EXCEPTIONS
# ============================================================


class StorageError(Exception):
    """Base exception for FarmNex storage failures."""


class StorageConfigurationError(StorageError):
    """Storage configuration is invalid."""


class StorageValidationError(StorageError):
    """Storage operation input is invalid."""


class StorageProviderError(StorageError):
    """The storage provider failed to complete an operation."""


class StorageNotFoundError(StorageError):
    """The requested storage object was not found."""


# ============================================================
# DATA TYPES
# ============================================================


@dataclass(frozen=True, slots=True)
class StoredObject:
    """
    Represents an object successfully stored by FarmNex.

    object_id:
        FarmNex-generated stable identifier for this storage object.

    bucket:
        Supabase Storage bucket containing the object.

    path:
        Object path inside the bucket.

    content_type:
        MIME type supplied for the object.

    size_bytes:
        Size of the uploaded object.
    """

    object_id: UUID
    bucket: str
    path: str
    content_type: str
    size_bytes: int


# ============================================================
# STORAGE SERVICE
# ============================================================


class StorageService:
    """
    Generic storage infrastructure service.

    This service is intentionally domain-agnostic.

    It does NOT contain rules for:
        - profile images
        - crop images
        - product images
        - farm images
        - KYC documents
        - invoices
        - delivery proofs

    Domain services decide those rules.

    This service only handles:
        - bucket validation
        - path validation
        - generic file validation
        - upload
        - replacement
        - download
        - delete
        - existence checks
        - signed URLs
        - listing
        - health checks

    Example:

        stored = await storage_service.upload(
            bucket="farmnex-storage",
            path="users/<user-id>/profile/<image-id>.webp",
            file_bytes=data,
            content_type="image/webp",
        )
    """

    # --------------------------------------------------------
    # Generic infrastructure limits
    # --------------------------------------------------------

    MAX_BUCKET_LENGTH = 100
    MAX_PATH_LENGTH = 1024

    _BUCKET_PATTERN = re.compile(
        r"^[a-z0-9][a-z0-9._-]{0,98}[a-z0-9]$|^[a-z0-9]$"
    )

    def __init__(self) -> None:
        self.client = get_supabase_client()

    # ========================================================
    # BUCKET VALIDATION
    # ========================================================

    @classmethod
    def validate_bucket(cls, bucket: str) -> str:
        """
        Validate a Supabase Storage bucket name.

        This validates only infrastructure syntax.
        The calling domain decides which bucket to use.
        """

        if not isinstance(bucket, str):
            raise StorageValidationError(
                "Storage bucket must be a string."
            )

        value = bucket.strip()

        if not value:
            raise StorageValidationError(
                "Storage bucket cannot be empty."
            )

        if len(value) > cls.MAX_BUCKET_LENGTH:
            raise StorageValidationError(
                "Storage bucket name is too long."
            )

        if "/" in value or "\\" in value:
            raise StorageValidationError(
                "Storage bucket must be a bucket name, not a path."
            )

        if not cls._BUCKET_PATTERN.fullmatch(value):
            raise StorageValidationError(
                "Invalid storage bucket name."
            )

        return value

    # ========================================================
    # PATH VALIDATION
    # ========================================================

    @classmethod
    def validate_path(cls, path: str) -> str:
        """
        Validate an object path inside a bucket.

        Domain services decide the semantic structure.

        Example:

            users/<user-id>/profile/<image-id>.webp

        This method only prevents unsafe paths.
        """

        if not isinstance(path, str):
            raise StorageValidationError(
                "Storage path must be a string."
            )

        value = path.strip()

        if not value:
            raise StorageValidationError(
                "Storage path cannot be empty."
            )

        if len(value) > cls.MAX_PATH_LENGTH:
            raise StorageValidationError(
                "Storage path is too long."
            )

        if "\\" in value:
            raise StorageValidationError(
                "Storage path cannot contain backslashes."
            )

        if value.startswith("/"):
            raise StorageValidationError(
                "Storage path cannot be absolute."
            )

        if "\x00" in value:
            raise StorageValidationError(
                "Storage path contains an invalid character."
            )

        parts = value.split("/")

        for part in parts:
            if not part:
                raise StorageValidationError(
                    "Storage path contains an empty path segment."
                )

            if part in {".", ".."}:
                raise StorageValidationError(
                    "Storage path contains an invalid path segment."
                )

        return "/".join(parts)

    # ========================================================
    # FILE VALIDATION
    # ========================================================

    @staticmethod
    def validate_file(
        *,
        file_bytes: bytes,
        content_type: str,
    ) -> str:
        """
        Generic storage-level file validation.

        IMPORTANT:
        This does not decide which MIME types a particular
        business operation accepts.

        Example:

            ProfileImageService:
                image/jpeg
                image/png
                image/webp

            KYCService:
                application/pdf
                image/jpeg
                image/png

        Those rules belong to their respective services.
        """

        if not isinstance(file_bytes, bytes):
            raise StorageValidationError(
                "File data must be bytes."
            )

        if not file_bytes:
            raise StorageValidationError(
                "The uploaded file is empty."
            )

        if not isinstance(content_type, str):
            raise StorageValidationError(
                "Content type must be a string."
            )

        normalized_type = content_type.strip().lower()

        if not normalized_type:
            raise StorageValidationError(
                "Content type cannot be empty."
            )

        if len(normalized_type) > 255:
            raise StorageValidationError(
                "Content type is too long."
            )

        # This is the universal infrastructure limit configured
        # in FarmNex settings.
        #
        # Domain services may apply a smaller limit.
        max_size = settings.storage_max_upload_size_bytes

        if len(file_bytes) > max_size:
            limit_mb = max_size / (1024 * 1024)

            raise StorageValidationError(
                f"File exceeds the global {limit_mb:g} MB "
                "storage upload limit."
            )

        return normalized_type

    # ========================================================
    # UPLOAD
    # ========================================================

    async def upload(
        self,
        *,
        bucket: str,
        path: str,
        file_bytes: bytes,
        content_type: str,
        cache_control_seconds: int = 3600,
    ) -> StoredObject:
        """
        Upload a new object.

        The caller supplies:
            bucket
            path
            file bytes
            content type

        Returns:
            StoredObject
        """

        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)

        content_type = self.validate_file(
            file_bytes=file_bytes,
            content_type=content_type,
        )

        if cache_control_seconds < 0:
            raise StorageValidationError(
                "Cache-Control value cannot be negative."
            )

        object_id = uuid4()

        file_options = {
            "content-type": content_type,
            "cache-control": str(cache_control_seconds),
            "upsert": "false",
        }

        try:
            await asyncio.to_thread(
                lambda: self.client.storage.from_(bucket).upload(
                    path,
                    file_bytes,
                    file_options=file_options,
                )
            )

        except Exception as exc:
            raise StorageProviderError(
                "Unable to upload the file to storage."
            ) from exc

        return StoredObject(
            object_id=object_id,
            bucket=bucket,
            path=path,
            content_type=content_type,
            size_bytes=len(file_bytes),
        )

    # ========================================================
    # REPLACE
    # ========================================================

    async def replace(
        self,
        *,
        bucket: str,
        old_path: str,
        new_path: str,
        file_bytes: bytes,
        content_type: str,
        cache_control_seconds: int = 3600,
    ) -> StoredObject:
        """
        Upload the new object first and then remove the old object.

        This prevents losing the old object when the new upload fails.
        """

        bucket = self.validate_bucket(bucket)

        old_path = self.validate_path(old_path)
        new_path = self.validate_path(new_path)

        if old_path == new_path:
            raise StorageValidationError(
                "Replacement object must use a different path."
            )

        # New object first.
        stored = await self.upload(
            bucket=bucket,
            path=new_path,
            file_bytes=file_bytes,
            content_type=content_type,
            cache_control_seconds=cache_control_seconds,
        )

        # Remove old object only after successful upload.
        try:
            await self.delete(
                bucket=bucket,
                path=old_path,
            )

        except StorageError:
            # New object is already stored.
            # The old object can be cleaned up separately.
            raise

        return stored

    # ========================================================
    # DOWNLOAD
    # ========================================================

    async def download(
        self,
        *,
        bucket: str,
        path: str,
    ) -> bytes:
        """
        Download an object.
        """

        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)

        try:
            response = await asyncio.to_thread(
                lambda: self.client.storage.from_(bucket).download(
                    path
                )
            )

        except Exception as exc:
            raise StorageProviderError(
                "Unable to download the file from storage."
            ) from exc

        if response is None:
            raise StorageNotFoundError(
                "Storage object was not found."
            )

        if not isinstance(response, bytes):
            raise StorageProviderError(
                "Storage provider returned invalid file data."
            )

        return response

    # ========================================================
    # SIGNED URL
    # ========================================================

    async def create_signed_url(
        self,
        *,
        bucket: str,
        path: str,
        expires_in: int | None = None,
    ) -> str:
        """
        Generate a temporary signed URL.
        """

        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)

        ttl = (
            expires_in
            if expires_in is not None
            else settings.storage_signed_url_expire_seconds
        )

        if ttl < 60 or ttl > 86400:
            raise StorageValidationError(
                "Signed URL expiry must be between "
                "60 and 86400 seconds."
            )

        try:
            response = await asyncio.to_thread(
                lambda: self.client.storage.from_(bucket)
                .create_signed_url(
                    path,
                    ttl,
                )
            )

        except Exception as exc:
            raise StorageProviderError(
                "Unable to create a signed storage URL."
            ) from exc

        if isinstance(response, dict):
            signed_url = (
                response.get("signedURL")
                or response.get("signedUrl")
                or response.get("signed_url")
            )

            if signed_url:
                return str(signed_url)

        signed_url = getattr(
            response,
            "signed_url",
            None,
        )

        if signed_url:
            return str(signed_url)

        raise StorageProviderError(
            "Storage provider returned no signed URL."
        )

    # ========================================================
    # DELETE
    # ========================================================

    async def delete(
        self,
        *,
        bucket: str,
        path: str,
    ) -> None:
        """
        Delete an object.
        """

        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)

        try:
            await asyncio.to_thread(
                lambda: self.client.storage.from_(bucket).remove(
                    [path]
                )
            )

        except Exception as exc:
            raise StorageProviderError(
                "Unable to delete the file from storage."
            ) from exc

    # ========================================================
    # EXISTS
    # ========================================================

    async def exists(
        self,
        *,
        bucket: str,
        path: str,
    ) -> bool:
        """
        Check whether an object exists.

        Supabase Storage does not provide a universal lightweight
        exists call, so the parent directory is listed and the
        filename is searched.
        """

        bucket = self.validate_bucket(bucket)
        path = self.validate_path(path)

        if "/" in path:
            parent = path.rsplit("/", 1)[0]
        else:
            parent = ""

        filename = path.rsplit("/", 1)[-1]

        try:
            response = await asyncio.to_thread(
                lambda: self.client.storage.from_(bucket).list(
                    parent,
                    {
                        "limit": 1000,
                    },
                )
            )

        except Exception as exc:
            raise StorageProviderError(
                "Unable to check storage object existence."
            ) from exc

        for item in response or []:
            if not isinstance(item, dict):
                continue

            if item.get("name") == filename:
                return True

        return False

    # ========================================================
    # LIST
    # ========================================================

    async def list_files(
        self,
        *,
        bucket: str,
        prefix: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        List objects under a prefix.
        """

        bucket = self.validate_bucket(bucket)

        if limit < 1 or limit > 1000:
            raise StorageValidationError(
                "limit must be between 1 and 1000."
            )

        if offset < 0:
            raise StorageValidationError(
                "offset cannot be negative."
            )

        normalized_prefix = prefix.strip("/")

        if normalized_prefix:
            normalized_prefix = self.validate_path(
                normalized_prefix
            )

        try:
            response = await asyncio.to_thread(
                lambda: self.client.storage.from_(bucket).list(
                    normalized_prefix,
                    {
                        "limit": limit,
                        "offset": offset,
                        "sortBy": {
                            "column": "name",
                            "order": "asc",
                        },
                    },
                )
            )

        except Exception as exc:
            raise StorageProviderError(
                "Unable to list storage files."
            ) from exc

        return list(response or [])

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    async def health_check(
        self,
        *,
        bucket: str,
    ) -> dict[str, Any]:
        """
        Verify that the specified storage bucket is reachable.
        """

        bucket = self.validate_bucket(bucket)

        try:
            result = await asyncio.to_thread(
                lambda: self.client.storage.from_(bucket).list(
                    "",
                    {
                        "limit": 1,
                    },
                )
            )

        except Exception as exc:
            raise StorageProviderError(
                "Unable to reach the configured storage bucket."
            ) from exc

        return {
            "provider": "supabase",
            "bucket": bucket,
            "reachable": True,
            "sample_count": len(result or []),
        }


# ============================================================
# SINGLETON
# ============================================================


storage_service = StorageService()


__all__ = [
    "StorageError",
    "StorageConfigurationError",
    "StorageValidationError",
    "StorageProviderError",
    "StorageNotFoundError",
    "StoredObject",
    "StorageService",
    "storage_service",
]