from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.farm import get_farm_service
from app.core.config import settings
from app.models.user import User
from app.schemas.farm_schema import (
    FarmCreateRequest,
    FarmFileResponse,
    FarmFileUrlResponse,
    FarmListResponse,
    FarmResponse,
    FarmUpdateRequest,
    MessageResponse,
)
from app.services.exceptions import (
    ConflictError,
    ForbiddenOperationError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.farm_service import FarmService


router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)


# ============================================================
# EXCEPTION TRANSLATION
# ============================================================


def _service_exception_to_http(
    exc: Exception,
) -> HTTPException:
    if isinstance(
        exc,
        ResourceNotFoundError,
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ResourceAlreadyExistsError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ConflictError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ForbiddenOperationError,
    ):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ValidationError,
    ):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to complete the requested operation.",
    )


# ============================================================
# LIST
# ============================================================


@router.get(
    "",
    response_model=FarmListResponse,
    status_code=status.HTTP_200_OK,
    summary="List my farms",
)
async def list_my_farms(
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of farms to skip.",
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of farms to return.",
    ),
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> FarmListResponse:
    try:
        items, total = await service.list_farms(
            current_user=current_user,
            offset=offset,
            limit=limit,
        )

        return FarmListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# GET ONE
# ============================================================


@router.get(
    "/{farm_public_id}",
    response_model=FarmResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my farm",
)
async def get_my_farm(
    farm_public_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> FarmResponse:
    try:
        return await service.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# CREATE
# ============================================================


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create my farm",
)
async def create_my_farm(
    payload: FarmCreateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> FarmResponse:
    try:
        return await service.create_farm(
            current_user=current_user,
            farm_data=payload.model_dump(exclude_unset=True),
        )

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# UPDATE
# ============================================================


@router.patch(
    "/{farm_public_id}",
    response_model=FarmResponse,
    status_code=status.HTTP_200_OK,
    summary="Update my farm",
)
async def update_my_farm(
    farm_public_id: UUID,
    payload: FarmUpdateRequest,
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> FarmResponse:
    try:
        return await service.update_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
            farm_data=payload.model_dump(exclude_unset=True),
        )
    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# FARM FILE - UPLOAD / REPLACE
# ============================================================


@router.post(
    "/{farm_public_id}/file",
    response_model=FarmFileResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload or replace my farm file",
)
async def upload_my_farm_file(
    farm_public_id: UUID,
    file: Annotated[
        UploadFile,
        File(
            description=(
                "JPEG, PNG, WebP, or PDF farm file."
            ),
        ),
    ],
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> FarmFileResponse:
    content_type = (
        file.content_type or ""
    ).strip().lower()

    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf",
    }

    if content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Only JPEG, PNG, WebP, and PDF "
                "farm files are allowed."
            ),
        )

    max_size = (
        settings.storage_max_upload_size_bytes
    )

    try:
        file_bytes = await file.read(
            max_size + 1
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read the uploaded file.",
        ) from exc
    finally:
        await file.close()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Farm file cannot be empty.",
        )

    if len(file_bytes) > max_size:
        limit_mb = max_size / (
            1024 * 1024
        )

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "Farm file exceeds the maximum "
                f"upload size of {limit_mb:g} MB."
            ),
        )

    try:
        farm, file_url = (
            await service.upload_farm_file(
                current_user=current_user,
                farm_public_id=farm_public_id,
                file_bytes=file_bytes,
                content_type=content_type,
            )
        )

        return FarmFileResponse(
            farm=farm,
            farm_file_url=file_url,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# FARM FILE - GET SIGNED URL
# ============================================================


@router.get(
    "/{farm_public_id}/file",
    response_model=FarmFileUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my farm file URL",
)
async def get_my_farm_file_url(
    farm_public_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> FarmFileUrlResponse:
    try:
        file_url = (
            await service.get_farm_file_url(
                current_user=current_user,
                farm_public_id=farm_public_id,
            )
        )

        return FarmFileUrlResponse(
            farm_file_url=file_url,
        )

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# FARM FILE - DOWNLOAD
# ============================================================


@router.get(
    "/{farm_public_id}/file/download",
    status_code=status.HTTP_200_OK,
    summary="Download my farm file",
)
async def download_my_farm_file(
    farm_public_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> Response:
    try:
        file_bytes, content_type = (
            await service.download_farm_file(
                current_user=current_user,
                farm_public_id=farm_public_id,
            )
        )

        return Response(
            content=file_bytes,
            media_type=content_type,
        )

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# FARM FILE - DELETE
# ============================================================


@router.delete(
    "/{farm_public_id}/file",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete my farm file",
)
async def delete_my_farm_file(
    farm_public_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> MessageResponse:
    try:
        await service.delete_farm_file(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

        return MessageResponse(
            message="Farm file deleted successfully.",
        )

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc


# ============================================================
# DELETE FARM
# ============================================================


@router.delete(
    "/{farm_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete my farm",
)
async def delete_my_farm(
    farm_public_id: UUID,
    current_user: User = Depends(
        get_current_user
    ),
    service: FarmService = Depends(
        get_farm_service
    ),
) -> None:
    try:
        await service.delete_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

    except Exception as exc:
        raise _service_exception_to_http(
            exc
        ) from exc