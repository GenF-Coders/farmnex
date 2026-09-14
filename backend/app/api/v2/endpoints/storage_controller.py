from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.api.dependencies.current_user import get_current_user
from app.models.user import User
from app.services.storage.exceptions import (
    StorageError,
    StorageProviderError,
    StorageValidationError,
)
from app.core.config import settings
from app.services.storage.service import storage_service


router = APIRouter(
    prefix="/storage",
    tags=["Storage"],
)


class StorageHealthResponse(BaseModel):
    provider: str
    bucket: str
    reachable: bool
    sample_count: int


class StorageTestUploadResponse(BaseModel):
    path: str
    content_type: str
    size_bytes: int
    signed_url: str
    signed_url_expires_in: int


class StorageDeleteResponse(BaseModel):
    deleted: bool
    path: str


@router.get(
    "/health",
    response_model=StorageHealthResponse,
    summary="Check storage connectivity",
)
async def storage_health() -> StorageHealthResponse:
    try:
        result = await storage_service.health_check()
        return StorageHealthResponse(**result)
    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage service is unavailable.",
        ) from exc


@router.post(
    "/test/upload",
    response_model=StorageTestUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a test image to storage",
)
async def storage_test_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> StorageTestUploadResponse:
    """Exercise upload + signed URL using the authenticated FarmNex user.

    This endpoint intentionally stores only under a dedicated test namespace.
    It must be removed before public production API exposure, or protected by
    a feature flag/admin permission once the storage integration is verified.
    """
    if not settings.storage_test_endpoints_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage test endpoints are disabled.",
        )

    try:
        content_type = (file.content_type or "").lower().strip()
        file_bytes = await file.read()

        path = storage_service.build_user_test_path(current_user.public_id, content_type)
        stored = await storage_service.upload(
            path=path,
            file_bytes=file_bytes,
            content_type=content_type,
        )
        signed_url = await storage_service.create_signed_url(path=path)

        return StorageTestUploadResponse(
            path=stored.path,
            content_type=stored.content_type,
            size_bytes=stored.size_bytes,
            signed_url=signed_url,
            signed_url_expires_in=settings.storage_signed_url_expire_seconds,
        )

    except StorageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to store the image.",
        ) from exc
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage operation failed.",
        ) from exc
    finally:
        await file.close()


class StorageDeleteRequest(BaseModel):
    path: str = Field(min_length=1, max_length=500)


@router.delete(
    "/test",
    response_model=StorageDeleteResponse,
    summary="Delete a test storage object",
)
async def storage_test_delete(
    payload: StorageDeleteRequest,
    current_user: User = Depends(get_current_user),
) -> StorageDeleteResponse:
    if not settings.storage_test_endpoints_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Storage test endpoints are disabled.",
        )

    expected_prefix = f"__storage_tests__/{current_user.public_id}/"

    if not payload.path.startswith(expected_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own storage test objects.",
        )

    try:
        await storage_service.delete(path=payload.path)
        return StorageDeleteResponse(
            deleted=True,
            path=payload.path,
        )
    except StorageProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to delete the storage object.",
        ) from exc
