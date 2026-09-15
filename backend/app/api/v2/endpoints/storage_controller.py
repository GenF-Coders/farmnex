from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.dependencies.current_user import get_current_user
from app.core.config import settings
from app.models.user import User
from app.services.storage_service import (
    StorageError,
    StorageNotFoundError,
    StorageProviderError,
    StorageValidationError,
    storage_service,
)


router = APIRouter(
    prefix="/storage",
    tags=["Storage"],
)


# ============================================================
# CONSTANTS
# ============================================================

# Temporary namespace used ONLY by this test controller.
#
# Later ProfileImageService, CropService, ProductService, etc.
# will generate their own domain-specific paths.
TEST_STORAGE_PREFIX = "__storage_tests__"


# ============================================================
# RESPONSE MODELS
# ============================================================


class StorageHealthResponse(BaseModel):
    provider: str
    bucket: str
    reachable: bool
    sample_count: int


class StorageTestUploadResponse(BaseModel):
    object_id: UUID
    bucket: str
    path: str
    content_type: str
    size_bytes: int
    signed_url: str
    signed_url_expires_in: int


class StorageSignedUrlResponse(BaseModel):
    bucket: str
    path: str
    signed_url: str
    signed_url_expires_in: int


class StorageDeleteRequest(BaseModel):
    bucket: str = Field(
        min_length=1,
        max_length=100,
    )

    path: str = Field(
        min_length=1,
        max_length=1024,
    )


class StorageDeleteResponse(BaseModel):
    deleted: bool
    bucket: str
    path: str


# ============================================================
# INTERNAL HELPERS
# ============================================================


def _ensure_test_endpoints_enabled() -> None:
    """
    Make sure temporary storage test endpoints are enabled.

    These endpoints should remain disabled in production.
    """

    if not settings.storage_test_endpoints_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage test endpoints are disabled.",
        )


def _test_prefix_for_user(
    user_public_id: UUID,
) -> str:
    """
    Return the test storage namespace for a user.

    Example:

        __storage_tests__/550e8400-e29b-41d4-a716-446655440000/
    """

    return (
        f"{TEST_STORAGE_PREFIX}/"
        f"{user_public_id}/"
    )


def _build_test_path(
    user_public_id: UUID,
    content_type: str,
) -> str:
    """
    Build a completely server-controlled storage path.

    The client never supplies the path.

    Example:

        __storage_tests__/{user_public_id}/{uuid}.webp
    """

    extension = _extension_from_content_type(
        content_type
    )

    return (
        f"{TEST_STORAGE_PREFIX}/"
        f"{user_public_id}/"
        f"{uuid4()}"
        f"{extension}"
    )


def _extension_from_content_type(
    content_type: str,
) -> str:
    """
    Convert MIME type to a test-only file extension.

    This logic belongs in the TEST controller.

    It does not belong in StorageService because the generic
    storage service should not contain domain/file-type rules.
    """

    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
        "text/plain": ".txt",
    }

    return mapping.get(
        content_type,
        ".bin",
    )


def _validate_test_object_access(
    *,
    current_user: User,
    bucket: str,
    path: str,
) -> None:
    """
    Ensure the authenticated user can only access objects
    created inside their own temporary test namespace.
    """

    # Only the configured FarmNex storage bucket can be used.
    if bucket != settings.storage_bucket:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid storage bucket.",
        )

    expected_prefix = _test_prefix_for_user(
        current_user.public_id
    )

    # Prevent one user from accessing another user's test files.
    if not path.startswith(expected_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You can only access your own "
                "storage test objects."
            ),
        )


# ============================================================
# HEALTH CHECK
# ============================================================


@router.get(
    "/health",
    response_model=StorageHealthResponse,
    summary="Check storage connectivity",
)
async def storage_health() -> StorageHealthResponse:
    """
    Check connectivity to the configured Supabase Storage bucket.

    Authentication is intentionally not required here because
    this is an infrastructure health check.
    """

    try:
        result = await storage_service.health_check(
            bucket=settings.storage_bucket,
        )

        return StorageHealthResponse(
            **result
        )

    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service is unavailable.",
        ) from exc

    except StorageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage configuration is invalid.",
        ) from exc

    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage health check failed.",
        ) from exc


# ============================================================
# TEST UPLOAD
# ============================================================


@router.post(
    "/test/upload",
    response_model=StorageTestUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a test file to storage",
)
async def storage_test_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> StorageTestUploadResponse:
    """
    Temporary storage integration test.

    Flow:

        Upload file
            ↓
        Generate test path
            ↓
        StorageService
            ↓
        Supabase Storage
            ↓
        Generate signed URL
            ↓
        Return storage object information

    Test objects are stored at:

        __storage_tests__/{user_public_id}/{uuid}.ext

    This endpoint is temporary and should be removed once
    storage integration testing is complete.
    """

    _ensure_test_endpoints_enabled()

    try:
        # ----------------------------------------------------
        # Content type
        # ----------------------------------------------------

        content_type = (
            file.content_type or ""
        ).strip().lower()

        if not content_type:
            raise StorageValidationError(
                "Uploaded file has no content type."
            )

        # ----------------------------------------------------
        # Read file
        # ----------------------------------------------------

        file_bytes = await file.read()

        if not file_bytes:
            raise StorageValidationError(
                "Uploaded file is empty."
            )

        # ----------------------------------------------------
        # Generate server-controlled test path
        # ----------------------------------------------------

        path = _build_test_path(
            user_public_id=current_user.public_id,
            content_type=content_type,
        )

        # ----------------------------------------------------
        # Upload through generic StorageService
        # ----------------------------------------------------

        stored = await storage_service.upload(
            bucket=settings.storage_bucket,
            path=path,
            file_bytes=file_bytes,
            content_type=content_type,
        )

        # ----------------------------------------------------
        # Generate signed URL
        # ----------------------------------------------------

        signed_url = await storage_service.create_signed_url(
            bucket=stored.bucket,
            path=stored.path,
        )

        # ----------------------------------------------------
        # Return result
        # ----------------------------------------------------

        return StorageTestUploadResponse(
            object_id=stored.object_id,
            bucket=stored.bucket,
            path=stored.path,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            signed_url=signed_url,
            signed_url_expires_in=(
                settings.storage_signed_url_expire_seconds
            ),
        )

    except StorageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to store the file.",
        ) from exc

    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage operation failed.",
        ) from exc

    finally:
        await file.close()


# ============================================================
# TEST SIGNED URL
# ============================================================


@router.post(
    "/test/signed-url",
    response_model=StorageSignedUrlResponse,
    summary="Create a signed URL for a test object",
)
async def storage_test_signed_url(
    bucket: str,
    path: str,
    current_user: User = Depends(get_current_user),
) -> StorageSignedUrlResponse:
    """
    Generate a temporary signed URL for a test object.
    """

    _ensure_test_endpoints_enabled()

    _validate_test_object_access(
        current_user=current_user,
        bucket=bucket,
        path=path,
    )

    try:
        signed_url = await storage_service.create_signed_url(
            bucket=bucket,
            path=path,
        )

        return StorageSignedUrlResponse(
            bucket=bucket,
            path=path,
            signed_url=signed_url,
            signed_url_expires_in=(
                settings.storage_signed_url_expire_seconds
            ),
        )

    except StorageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to create signed URL.",
        ) from exc

    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage operation failed.",
        ) from exc



# ============================================================
# TEST DOWNLOAD
# ============================================================


def _get_download_filename_and_media_type(
    path: str,
) -> tuple[str, str]:
    """
    Build a safe download filename and determine the correct
    HTTP media type from the server-generated storage path.

    Expected test path:

        __storage_tests__/{user_public_id}/{file_uuid}.png

    Example:

        __storage_tests__/
        d7909735-8db3-40fa-b6b9-c5d1157e02c3/
        ef8ad9f4-4761-40e7-ab01-f037179e0824.png

    Returns:

        (
            "ef8ad9f4-4761-40e7-ab01-f037179e0824.png",
            "image/png",
        )
    """

    # Get only the final filename from the storage path.
    # This prevents the bucket/path from being exposed as
    # the download filename.
    filename = path.rsplit("/", 1)[-1]

    if not filename or "." not in filename:
        raise StorageValidationError(
            "Storage object filename is invalid."
        )

    # Separate UUID and extension.
    object_id_text, extension = filename.rsplit(".", 1)

    extension = extension.lower()

    # The test controller generates UUID filenames.
    try:
        object_id = UUID(object_id_text)
    except (ValueError, TypeError, AttributeError) as exc:
        raise StorageValidationError(
            "Storage object filename is invalid."
        ) from exc

    # Only allow MIME types supported by the test upload endpoint.
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "pdf": "application/pdf",
        "txt": "text/plain",
    }

    media_type = media_types.get(extension)

    if media_type is None:
        raise StorageValidationError(
            "Unsupported storage object type."
        )

    # Rebuild the filename from the validated UUID rather than
    # trusting arbitrary path text supplied by the client.
    safe_filename = f"{object_id}.{extension}"

    return safe_filename, media_type


@router.get(
    "/test/download",
    summary="Download a test storage object",
)
async def storage_test_download(
    bucket: str,
    path: str,
    current_user: User = Depends(get_current_user),
) -> Response:
    """
    Download a test object through FarmNex.

    Security:
        - Test endpoints must be enabled.
        - Only the configured FarmNex storage bucket is allowed.
        - Users can only access their own test-storage namespace.

    The response uses the correct MIME type and a UUID-based
    filename instead of exposing the complete storage path.
    """

    _ensure_test_endpoints_enabled()

    _validate_test_object_access(
        current_user=current_user,
        bucket=bucket,
        path=path,
    )

    try:
        # --------------------------------------------------------
        # Download actual file bytes from Supabase Storage
        # --------------------------------------------------------

        file_bytes = await storage_service.download(
            bucket=bucket,
            path=path,
        )

        # --------------------------------------------------------
        # Determine safe filename + correct MIME type
        # --------------------------------------------------------

        download_filename, media_type = (
            _get_download_filename_and_media_type(path)
        )

        # --------------------------------------------------------
        # Return actual file
        # --------------------------------------------------------

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": (
                    f'attachment; filename="{download_filename}"'
                )
            },
        )

    except StorageNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage object was not found.",
        ) from exc

    except StorageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to download the storage object.",
        ) from exc

    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage operation failed.",
        ) from exc
        
        
        
        

# ============================================================
# TEST DELETE
# ============================================================


@router.delete(
    "/test",
    response_model=StorageDeleteResponse,
    summary="Delete a test storage object",
)
async def storage_test_delete(
    payload: StorageDeleteRequest,
    current_user: User = Depends(get_current_user),
) -> StorageDeleteResponse:
    """
    Delete a test storage object.

    A user can only delete objects under:

        __storage_tests__/{their_user_public_id}/
    """

    _ensure_test_endpoints_enabled()

    _validate_test_object_access(
        current_user=current_user,
        bucket=payload.bucket,
        path=payload.path,
    )

    try:
        await storage_service.delete(
            bucket=payload.bucket,
            path=payload.path,
        )

        return StorageDeleteResponse(
            deleted=True,
            bucket=payload.bucket,
            path=payload.path,
        )

    except StorageNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage object was not found.",
        ) from exc

    except StorageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to delete the storage object.",
        ) from exc

    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage operation failed.",
        ) from exc