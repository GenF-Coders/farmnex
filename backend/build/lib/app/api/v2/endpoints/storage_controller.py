from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.services.storage_service import StorageError, StorageProviderError, storage_service

router = APIRouter(prefix="/storage", tags=["Storage"])


class StorageHealthResponse(BaseModel):
    provider: str
    bucket: str
    reachable: bool
    sample_count: int


@router.get("/health", response_model=StorageHealthResponse, summary="Check storage connectivity")
async def storage_health() -> StorageHealthResponse:
    try:
        return StorageHealthResponse(**await storage_service.health_check(bucket=settings.storage_bucket))
    except StorageProviderError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Storage service is unavailable.") from exc
    except StorageError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Storage health check failed.") from exc
