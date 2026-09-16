from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any, ClassVar
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.supabase import get_supabase_client


logger = logging.getLogger(__name__)


# ============================================================
# EXCEPTIONS
# ============================================================


class StorageError(Exception):
    """Base exception for all FarmNex storage errors."""


class StorageConfigurationError(StorageError):
    """Storage configuration or client initialization error."""


class StorageValidationError(StorageError):
    """Invalid storage argument or uploaded file."""


class StorageProviderError(StorageError):
    """Supabase Storage provider operation failed."""

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        bucket: str | None = None,
        path: str | None = None,
        status: int | str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)

        self.operation = operation
        self.bucket = bucket
        self.path = path
        self.status = status
        self.code = code


class StorageNotFoundError(StorageError):
    """Requested storage object does not exist."""


# ============================================================
# RESULT TYPE
# ============================================================


@dataclass(frozen=True, slots=True)
class StoredObject:
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
    Centralized FarmNex storage service.

    Supabase Storage is accessed only through this service.

    Bucket:

        storage-bucket

    Required FarmNex folder layout:

        storage-bucket/
        ├── profile_image/
        ├── farm-images/
        ├── farm-files/
        ├── crop-images/
        ├── product-images/
        ├── kyc-documents/
        ├── delivery-proof/
        └── invoices/

    New application uploads MUST use:

        <folder>/<uuid>.<extension>

    Examples:

        profile_image/550e8400-e29b-41d4-a716-446655440000.webp
        farm-images/550e8400-e29b-41d4-a716-446655440000.jpg
        farm-files/550e8400-e29b-41d4-a716-446655440000.pdf

    No user ID, farm ID, or other nested ownership path is generated
    by this service.

    The bucket itself must already exist in Supabase Storage.
    """

    # --------------------------------------------------------
    # General limits
    # --------------------------------------------------------

    MAX_BUCKET_LENGTH: ClassVar[int] = 100
    MAX_PATH_LENGTH: ClassVar[int] = 1024
    MAX_FILENAME_LENGTH: ClassVar[int] = 255

    MIN_SIGNED_URL_SECONDS: ClassVar[int] = 60
    MAX_SIGNED_URL_SECONDS: ClassVar[int] = 86400

    DEFAULT_CACHE_CONTROL_SECONDS: ClassVar[int] = 3600

    # --------------------------------------------------------
    # Validation patterns
    # --------------------------------------------------------

    _BUCKET_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^[a-z0-9](?:[a-z0-9._-]{0,98}[a-z0-9])?$"
    )

    _FOLDER_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$"
    )

    _FILENAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^[A-Za-z0-9][A-Za-z0-9._-]{0,254}$"
    )

    # --------------------------------------------------------
    # FarmNex storage folders
    # --------------------------------------------------------

    FOLDERS: ClassVar[frozenset[str]] = frozenset(
        {
            "profile_image",
            "farm-images",
            "farm-files",
            "crop-images",
            "product-images",
            "kyc-documents",
            "delivery-proof",
            "invoices",
        }
    )

    # --------------------------------------------------------
    # Supported file extensions
    # --------------------------------------------------------

    _EXTENSIONS: ClassVar[dict[str, str]] = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "application/pdf": "pdf",
    }

    # --------------------------------------------------------
    # File signatures
    # --------------------------------------------------------

    _MAGIC_SIGNATURES: ClassVar[
        dict[str, tuple[bytes, ...]]
    ] = {
        "image/jpeg": (
            b"\xff\xd8\xff",
        ),
        "image/png": (
            b"\x89PNG\r\n\x1a\n",
        ),
        "image/webp": (
            b"RIFF",
        ),
        "application/pdf": (
            b"%PDF-",
        ),
    }

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        # Lazy initialization prevents storage configuration from
        # being unnecessarily initialized during application import.
        self._client: Any | None = None

    @property
    def client(self) -> Any:
        """
        Return the configured Supabase client.

        The client is initialized lazily and then reused by this
        process.
        """

        if self._client is None:
            try:
                self._client = get_supabase_client()
            except StorageError:
                raise
            except Exception as exc:
                logger.exception(
                    "Unable to initialize Supabase storage client."
                )

                raise StorageConfigurationError(
                    "Supabase storage client could not be initialized."
                ) from exc

        return self._client

    # ========================================================
    # CONFIGURATION
    # ========================================================

    @classmethod
    def _configured_bucket(cls) -> str:
        bucket = getattr(
            settings,
            "storage_bucket",
            None,
        )

        if not isinstance(bucket, str) or not bucket.strip():
            raise StorageConfigurationError(
                "Storage bucket is not configured."
            )

        return cls.validate_bucket(bucket)

    @classmethod
    def validate_bucket(
        cls,
        bucket: str,
    ) -> str:
        if not isinstance(bucket, str):
            raise StorageValidationError(
                "Storage bucket must be a string."
            )

        value = bucket.strip()

        if (
            not value
            or len(value) > cls.MAX_BUCKET_LENGTH
            or not cls._BUCKET_PATTERN.fullmatch(value)
        ):
            raise StorageValidationError(
                "Invalid storage bucket name."
            )

        return value

    # ========================================================
    # FOLDER VALIDATION
    # ========================================================

    @classmethod
    def validate_folder(
        cls,
        folder: str,
    ) -> str:
        if not isinstance(folder, str):
            raise StorageValidationError(
                "Storage folder must be a string."
            )

        value = folder.strip().strip("/")

        if (
            not value
            or not cls._FOLDER_PATTERN.fullmatch(value)
        ):
            raise StorageValidationError(
                "Invalid storage folder name."
            )

        if value not in cls.FOLDERS:
            raise StorageValidationError(
                f"Unsupported storage folder: {value}."
            )

        return value

    # ========================================================
    # FILENAME VALIDATION
    # ========================================================

    @classmethod
    def validate_filename(
        cls,
        filename: str,
    ) -> str:
        if not isinstance(filename, str):
            raise StorageValidationError(
                "Storage filename must be a string."
            )

        value = filename.strip()

        if (
            not value
            or len(value) > cls.MAX_FILENAME_LENGTH
            or value in {".", ".."}
            or "/" in value
            or "\\" in value
            or "\x00" in value
            or not cls._FILENAME_PATTERN.fullmatch(value)
        ):
            raise StorageValidationError(
                "Invalid storage filename."
            )

        return value

    # ========================================================
    # PATH BUILDING
    # ========================================================

    @classmethod
    def build_path(
        cls,
        *,
        folder: str,
        filename: str,
    ) -> str:
        """
        Build an approved FarmNex storage path.

        Result:

            <folder>/<filename>
        """

        folder = cls.validate_folder(folder)
        filename = cls.validate_filename(filename)

        return f"{folder}/{filename}"

    @classmethod
    def build_uuid_path(
        cls,
        *,
        folder: str,
        content_type: str,
    ) -> str:
        """
        Generate a FarmNex UUID-based object path.

        Example:

            profile_image/<uuid>.webp
        """

        folder = cls.validate_folder(folder)

        extension = cls.extension_for_content_type(
            content_type
        )

        filename = f"{uuid4()}.{extension}"

        return cls.build_path(
            folder=folder,
            filename=filename,
        )

    # ========================================================
    # CONTENT TYPE
    # ========================================================

    @classmethod
    def normalize_content_type(
        cls,
        content_type: str,
    ) -> str:
        if not isinstance(content_type, str):
            raise StorageValidationError(
                "Uploaded file has no content type."
            )

        normalized = (
            content_type
            .strip()
            .lower()
            .split(";", 1)[0]
            .strip()
        )

        if (
            not normalized
            or "/" not in normalized
            or len(normalized) > 127
        ):
            raise StorageValidationError(
                "Uploaded file has no valid content type."
            )

        return normalized

    @classmethod
    def extension_for_content_type(
        cls,
        content_type: str,
    ) -> str:
        normalized = cls.normalize_content_type(
            content_type
        )

        extension = cls._EXTENSIONS.get(
            normalized
        )

        if extension is None:
            raise StorageValidationError(
                f"Unsupported storage content type: "
                f"{normalized}."
            )

        return extension

    # ========================================================
    # PATH VALIDATION
    # ========================================================

    @classmethod
    def validate_path(
        cls,
        path: str,
    ) -> str:
        """
        Validate an existing provider path.

        This permits nested paths for compatibility with existing
        objects, but rejects traversal and malformed paths.
        """

        if not isinstance(path, str):
            raise StorageValidationError(
                "Storage path must be a string."
            )

        value = path.strip()

        if (
            not value
            or len(value) > cls.MAX_PATH_LENGTH
        ):
            raise StorageValidationError(
                "Invalid storage path."
            )

        if (
            value.startswith("/")
            or value.endswith("/")
            or "\\" in value
            or "\x00" in value
        ):
            raise StorageValidationError(
                "Invalid storage path."
            )

        parts = value.split("/")

        for part in parts:
            if (
                not part
                or part in {".", ".."}
                or "\x00" in part
            ):
                raise StorageValidationError(
                    "Invalid storage path."
                )

        return value

    @classmethod
    def validate_managed_path(
        cls,
        path: str,
    ) -> str:
        """
        Validate a new FarmNex application upload path.

        New files MUST be:

            <approved-folder>/<filename>
        """

        value = cls.validate_path(path)

        parts = value.split("/")

        if (
            len(parts) != 2
            or parts[0] not in cls.FOLDERS
        ):
            raise StorageValidationError(
                "New storage objects must use one "
                "configured top-level folder."
            )

        cls.validate_folder(parts[0])
        cls.validate_filename(parts[1])

        return value

    # ========================================================
    # FILE VALIDATION
    # ========================================================

    @classmethod
    def validate_file(
        cls,
        *,
        file_bytes: bytes,
        content_type: str,
        verify_signature: bool = True,
    ) -> str:
        """
        Validate uploaded file bytes and return normalized MIME type.

        Checks:

        - bytes type
        - non-empty file
        - configured size limit
        - valid MIME type
        - actual file signature for known supported formats
        """

        if not isinstance(file_bytes, bytes):
            raise StorageValidationError(
                "Uploaded file data must be bytes."
            )

        if not file_bytes:
            raise StorageValidationError(
                "The uploaded file is empty."
            )

        normalized = cls.normalize_content_type(
            content_type
        )

        max_size = getattr(
            settings,
            "storage_max_upload_size_bytes",
            None,
        )

        if (
            not isinstance(max_size, int)
            or max_size <= 0
        ):
            raise StorageConfigurationError(
                "Storage upload size limit must be "
                "greater than zero."
            )

        if len(file_bytes) > max_size:
            limit_mb = max_size / (
                1024 * 1024
            )

            raise StorageValidationError(
                f"File exceeds the {limit_mb:g} MB "
                "upload limit."
            )

        if verify_signature:
            cls.validate_file_signature(
                file_bytes=file_bytes,
                content_type=normalized,
            )

        return normalized

    @classmethod
    def validate_file_signature(
        cls,
        *,
        file_bytes: bytes,
        content_type: str,
    ) -> None:
        """
        Validate actual file bytes against the declared MIME type.

        This public method intentionally exists because domain services
        may call it explicitly.

        Supported signatures:

        JPEG
        PNG
        WebP
        PDF
        """

        if not isinstance(file_bytes, bytes):
            raise StorageValidationError(
                "Uploaded file data must be bytes."
            )

        if not file_bytes:
            raise StorageValidationError(
                "The uploaded file is empty."
            )

        normalized = cls.normalize_content_type(
            content_type
        )

        # No signature rule means the domain service may still decide
        # whether the MIME type is acceptable.
        signatures = cls._MAGIC_SIGNATURES.get(
            normalized
        )

        if signatures is None:
            return

        if not cls._matches_signature(
            file_bytes=file_bytes,
            content_type=normalized,
        ):
            raise StorageValidationError(
                "Uploaded file content does not "
                "match its content type."
            )

    @classmethod
    def _matches_signature(
        cls,
        *,
        file_bytes: bytes,
        content_type: str,
    ) -> bool:
        if content_type == "image/webp":
            return (
                len(file_bytes) >= 12
                and file_bytes[:4] == b"RIFF"
                and file_bytes[8:12] == b"WEBP"
            )

        signatures = cls._MAGIC_SIGNATURES.get(
            content_type,
            (),
        )

        return any(
            file_bytes.startswith(signature)
            for signature in signatures
        )

    # ========================================================
    # PROVIDER ERROR EXTRACTION
    # ========================================================

    @staticmethod
    def _provider_details(
        exc: Exception,
    ) -> tuple[
        int | str | None,
        str | None,
        str,
    ]:
        status = getattr(
            exc,
            "status",
            None,
        )

        code = getattr(
            exc,
            "code",
            None,
        )

        message = (
            getattr(
                exc,
                "message",
                None,
            )
            or str(exc)
            or exc.__class__.__name__
        )

        return (
            status,
            code,
            message,
        )

    @classmethod
    def _raise_provider_error(
        cls,
        *,
        operation: str,
        bucket: str,
        path: str | None,
        exc: Exception,
    ) -> None:
        status, code, provider_message = (
            cls._provider_details(exc)
        )

        logger.error(
            "Supabase Storage %s failed | "
            "bucket=%s | path=%s | status=%s | "
            "code=%s | message=%s",
            operation,
            bucket,
            path,
            status,
            code,
            provider_message,
            exc_info=True,
        )

        status_value: int | None = None

        try:
            if status is not None:
                status_value = int(status)
        except (
            TypeError,
            ValueError,
        ):
            status_value = None

        normalized_code = str(
            code or ""
        ).lower()

        if (
            status_value == 404
            or normalized_code
            in {
                "not_found",
                "object_not_found",
                "storage_object_not_found",
            }
        ):
            raise StorageNotFoundError(
                "Storage object was not found."
            ) from exc

        raise StorageProviderError(
            f"Storage provider failed during "
            f"{operation}.",
            operation=operation,
            bucket=bucket,
            path=path,
            status=status,
            code=code,
        ) from exc

    # ========================================================
    # UPLOAD
    # ========================================================

    async def upload(
        self,
        *,
        bucket: str | None = None,
        path: str,
        file_bytes: bytes,
        content_type: str,
        cache_control_seconds: int = DEFAULT_CACHE_CONTROL_SECONDS,
        upsert: bool = False,
        verify_signature: bool = True,
    ) -> StoredObject:
        """
        Upload a new object.

        New uploads are restricted to the FarmNex flat folder layout.
        """

        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        path = self.validate_managed_path(
            path
        )

        content_type = self.validate_file(
            file_bytes=file_bytes,
            content_type=content_type,
            verify_signature=verify_signature,
        )

        if (
            not isinstance(
                cache_control_seconds,
                int,
            )
            or cache_control_seconds < 0
        ):
            raise StorageValidationError(
                "Invalid storage cache-control value."
            )

        if not isinstance(
            upsert,
            bool,
        ):
            raise StorageValidationError(
                "Storage upsert must be boolean."
            )

        file_options = {
            "content-type": content_type,
            "cache-control": str(
                cache_control_seconds
            ),
            "upsert": "true"
            if upsert
            else "false",
        }

        try:
            await asyncio.to_thread(
                lambda: (
                    self.client.storage
                    .from_(bucket)
                    .upload(
                        path,
                        file_bytes,
                        file_options=file_options,
                    )
                )
            )

        except Exception as exc:
            self._raise_provider_error(
                operation="upload",
                bucket=bucket,
                path=path,
                exc=exc,
            )

        return StoredObject(
            object_id=uuid4(),
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
        bucket: str | None = None,
        old_path: str,
        new_path: str,
        file_bytes: bytes,
        content_type: str,
        cache_control_seconds: int = DEFAULT_CACHE_CONTROL_SECONDS,
        verify_signature: bool = True,
    ) -> StoredObject:
        """
        Replace an existing object safely.

        Sequence:

            1. Upload new object.
            2. Caller can persist new DB reference.
            3. Attempt cleanup of old object.

        Failure to delete the old object does NOT invalidate the
        newly uploaded object.
        """

        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        old_path = self.validate_path(
            old_path
        )

        new_path = self.validate_managed_path(
            new_path
        )

        if old_path == new_path:
            raise StorageValidationError(
                "Replacement object must use a different path."
            )

        stored = await self.upload(
            bucket=bucket,
            path=new_path,
            file_bytes=file_bytes,
            content_type=content_type,
            cache_control_seconds=cache_control_seconds,
            upsert=False,
            verify_signature=verify_signature,
        )

        try:
            await self.delete(
                bucket=bucket,
                path=old_path,
            )

        except StorageNotFoundError:
            # Already gone; replacement is successful.
            pass

        except StorageError:
            logger.warning(
                "Storage replacement succeeded but "
                "old object cleanup failed | "
                "bucket=%s | old_path=%s | new_path=%s",
                bucket,
                old_path,
                new_path,
                exc_info=True,
            )

        return stored

    # ========================================================
    # DOWNLOAD
    # ========================================================

    async def download(
        self,
        *,
        bucket: str | None = None,
        path: str,
    ) -> bytes:
        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        path = self.validate_path(
            path
        )

        try:
            response = await asyncio.to_thread(
                lambda: (
                    self.client.storage
                    .from_(bucket)
                    .download(path)
                )
            )

        except Exception as exc:
            self._raise_provider_error(
                operation="download",
                bucket=bucket,
                path=path,
                exc=exc,
            )

        if response is None:
            raise StorageNotFoundError(
                "Storage object was not found."
            )

        if not isinstance(
            response,
            bytes,
        ):
            raise StorageProviderError(
                "Storage provider returned invalid "
                "file data.",
                operation="download",
                bucket=bucket,
                path=path,
            )

        return response

    # ========================================================
    # SIGNED URL
    # ========================================================

    async def create_signed_url(
        self,
        *,
        bucket: str | None = None,
        path: str,
        expires_in: int | None = None,
    ) -> str:
        """
        Create a temporary signed URL.

        This is the correct access mechanism for objects in
        a private Supabase bucket.
        """

        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        path = self.validate_path(
            path
        )

        ttl = (
            getattr(
                settings,
                "storage_signed_url_expire_seconds",
                900,
            )
            if expires_in is None
            else expires_in
        )

        if not isinstance(
            ttl,
            int,
        ):
            raise StorageValidationError(
                "Signed URL expiry must be an integer."
            )

        if not (
            self.MIN_SIGNED_URL_SECONDS
            <= ttl
            <= self.MAX_SIGNED_URL_SECONDS
        ):
            raise StorageValidationError(
                "Signed URL expiry must be between "
                "60 and 86400 seconds."
            )

        try:
            response = await asyncio.to_thread(
                lambda: (
                    self.client.storage
                    .from_(bucket)
                    .create_signed_url(
                        path,
                        ttl,
                    )
                )
            )

        except Exception as exc:
            self._raise_provider_error(
                operation="create_signed_url",
                bucket=bucket,
                path=path,
                exc=exc,
            )

        value: Any = None

        if isinstance(
            response,
            dict,
        ):
            value = (
                response.get("signedURL")
                or response.get("signedUrl")
                or response.get("signed_url")
            )

        else:
            value = (
                getattr(
                    response,
                    "signed_url",
                    None,
                )
                or getattr(
                    response,
                    "signedURL",
                    None,
                )
                or getattr(
                    response,
                    "signedUrl",
                    None,
                )
            )

        if not isinstance(
            value,
            str,
        ) or not value:
            logger.error(
                "Supabase Storage returned no signed URL | "
                "bucket=%s | path=%s | response_type=%s",
                bucket,
                path,
                type(response).__name__,
            )

            raise StorageProviderError(
                "Storage provider returned no signed URL.",
                operation="create_signed_url",
                bucket=bucket,
                path=path,
            )

        return value

    # ========================================================
    # GET SIGNED URL ALIAS
    # ========================================================

    async def get(
        self,
        *,
        bucket: str | None = None,
        path: str,
        expires_in: int | None = None,
    ) -> str:
        return await self.create_signed_url(
            bucket=bucket,
            path=path,
            expires_in=expires_in,
        )

    # ========================================================
    # DELETE
    # ========================================================

    async def delete(
        self,
        *,
        bucket: str | None = None,
        path: str,
    ) -> None:
        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        path = self.validate_path(
            path
        )

        try:
            response = await asyncio.to_thread(
                lambda: (
                    self.client.storage
                    .from_(bucket)
                    .remove([path])
                )
            )

        except Exception as exc:
            self._raise_provider_error(
                operation="delete",
                bucket=bucket,
                path=path,
                exc=exc,
            )

        if isinstance(
            response,
            dict,
        ):
            if response.get("error"):
                raise StorageProviderError(
                    "Storage provider failed during delete.",
                    operation="delete",
                    bucket=bucket,
                    path=path,
                )

    # ========================================================
    # EXISTS
    # ========================================================

    async def exists(
        self,
        *,
        bucket: str | None = None,
        path: str,
    ) -> bool:
        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        path = self.validate_path(
            path
        )

        try:
            result = await asyncio.to_thread(
                lambda: (
                    self.client.storage
                    .from_(bucket)
                    .exists(path)
                )
            )

        except Exception as exc:
            self._raise_provider_error(
                operation="exists",
                bucket=bucket,
                path=path,
                exc=exc,
            )

        return bool(result)

    # ========================================================
    # LIST
    # ========================================================

    async def list_files(
        self,
        *,
        bucket: str | None = None,
        prefix: str = "",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        if (
            not isinstance(limit, int)
            or not 1 <= limit <= 1000
        ):
            raise StorageValidationError(
                "Storage list limit must be between "
                "1 and 1000."
            )

        if (
            not isinstance(offset, int)
            or offset < 0
        ):
            raise StorageValidationError(
                "Storage list offset must be non-negative."
            )

        prefix = prefix.strip().strip("/")

        if prefix:
            prefix = self.validate_path(
                prefix
            )

        options = {
            "limit": limit,
            "offset": offset,
            "sortBy": {
                "column": "name",
                "order": "asc",
            },
        }

        try:
            response = await asyncio.to_thread(
                lambda: (
                    self.client.storage
                    .from_(bucket)
                    .list(
                        prefix,
                        options,
                    )
                )
            )

        except Exception as exc:
            self._raise_provider_error(
                operation="list",
                bucket=bucket,
                path=prefix or None,
                exc=exc,
            )

        if response is None:
            return []

        if not isinstance(
            response,
            list,
        ):
            raise StorageProviderError(
                "Storage provider returned invalid "
                "list data.",
                operation="list",
                bucket=bucket,
                path=prefix or None,
            )

        return [
            item
            for item in response
            if isinstance(item, dict)
        ]

    # ========================================================
    # HEALTH CHECK
    # ========================================================

    async def health_check(
        self,
        *,
        bucket: str | None = None,
    ) -> dict[str, Any]:
        """
        Perform a real authenticated Storage API request.

        This verifies:

            FastAPI
              ↓
            Supabase client
              ↓
            Supabase URL
              ↓
            server-side key
              ↓
            storage bucket
        """

        bucket = self.validate_bucket(
            bucket or self._configured_bucket()
        )

        try:
            result = await asyncio.to_thread(
                lambda: (
                    self.client.storage
                    .from_(bucket)
                    .list(
                        "",
                        {
                            "limit": 1,
                            "offset": 0,
                        },
                    )
                )
            )

        except Exception as exc:
            self._raise_provider_error(
                operation="health_check",
                bucket=bucket,
                path=None,
                exc=exc,
            )

        if result is None:
            sample_count = 0

        elif isinstance(
            result,
            list,
        ):
            sample_count = len(result)

        else:
            raise StorageProviderError(
                "Storage provider returned invalid "
                "health-check data.",
                operation="health_check",
                bucket=bucket,
            )

        return {
            "provider": "supabase",
            "bucket": bucket,
            "reachable": True,
            "sample_count": sample_count,
        }


# ============================================================
# SINGLE APPLICATION INSTANCE
# ============================================================


storage_service = StorageService()


# ============================================================
# PUBLIC API
# ============================================================


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