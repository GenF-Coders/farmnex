from __future__ import annotations

from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import (
    get_current_user,
)
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.schemas.farm_schema import (
    FarmCreateRequest,
    FarmFileUrlResponse,
    FarmListResponse,
    FarmResponse,
    FarmUpdateRequest,
    MessageResponse,
)
from app.services.farm_service import FarmService


router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)


def _get_farm_service(
    db: AsyncSession,
) -> FarmService:
    return FarmService(
        repository=FarmRepository(db),
    )


def _exception_response(
    exc: AppException,
):
    content = {
        "detail": exc.detail,
    }

    if exc.code:
        content["code"] = exc.code

    if exc.data is not None:
        content["data"] = exc.data

    return Response(
        content=None,
    )


# ================================================================
# CREATE
# ================================================================


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_farm(
    payload: FarmCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmResponse:
    service = _get_farm_service(db)

    farm = await service.create_farm(
        user_id=current_user.id,
        farm_data=payload.model_dump(),
    )

    data = await service.build_farm_response_data(
        farm
    )

    return FarmResponse.model_validate(data)


# ================================================================
# LIST
# ================================================================


@router.get(
    "",
    response_model=FarmListResponse,
)
async def list_farms(
    offset: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmListResponse:
    service = _get_farm_service(db)

    farms, total = await service.list_farms(
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )

    items = []

    for farm in farms:
        data = await service.build_farm_response_data(
            farm
        )

        items.append(
            FarmResponse.model_validate(data)
        )

    return FarmListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


# ================================================================
# GET
# ================================================================


@router.get(
    "/{farm_public_id}",
    response_model=FarmResponse,
)
async def get_farm(
    farm_public_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmResponse:
    service = _get_farm_service(db)

    farm = await service.get_farm(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    data = await service.build_farm_response_data(
        farm
    )

    return FarmResponse.model_validate(data)


# ================================================================
# UPDATE
# ================================================================


@router.patch(
    "/{farm_public_id}",
    response_model=FarmResponse,
)
async def update_farm(
    farm_public_id: UUID,
    payload: FarmUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmResponse:
    service = _get_farm_service(db)

    farm = await service.update_farm(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
        farm_data=payload.model_dump(
            exclude_unset=True
        ),
    )

    data = await service.build_farm_response_data(
        farm
    )

    return FarmResponse.model_validate(data)


# ================================================================
# DELETE FARM
# ================================================================


@router.delete(
    "/{farm_public_id}",
    response_model=MessageResponse,
)
async def delete_farm(
    farm_public_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    service = _get_farm_service(db)

    await service.delete_farm(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    return MessageResponse(
        message="Farm deleted successfully."
    )


# ================================================================
# UPLOAD / REPLACE FARM FILE
# ================================================================


@router.post(
    "/{farm_public_id}/file",
    response_model=FarmResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_or_replace_farm_file(
    farm_public_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmResponse:
    service = _get_farm_service(db)

    file_bytes = await file.read()

    await service.upload_farm_file(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
        file_bytes=file_bytes,
        content_type=(
            file.content_type
            or "application/octet-stream"
        ),
        filename=file.filename,
    )

    # Fetch fresh DB state after upload.
    farm = await service.get_farm(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    data = await service.build_farm_response_data(
        farm
    )

    return FarmResponse.model_validate(data)


# ================================================================
# GET FARM FILE URL
# ================================================================


@router.get(
    "/{farm_public_id}/file",
    response_model=FarmFileUrlResponse,
)
async def get_farm_file_url(
    farm_public_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FarmFileUrlResponse:
    service = _get_farm_service(db)

    url, content_type = (
        await service.get_farm_file_url(
            user_id=current_user.id,
            farm_public_id=farm_public_id,
        )
    )

    return FarmFileUrlResponse(
        farm_file_url=url,
        farm_file_content_type=content_type,
    )


# ================================================================
# DOWNLOAD FARM FILE
# ================================================================


@router.get(
    "/{farm_public_id}/file/download",
)
async def download_farm_file(
    farm_public_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    service = _get_farm_service(db)

    file_bytes, content_type = (
        await service.download_farm_file(
            user_id=current_user.id,
            farm_public_id=farm_public_id,
        )
    )

    return Response(
        content=file_bytes,
        media_type=content_type,
    )


# ================================================================
# DELETE FARM FILE
# ================================================================


@router.delete(
    "/{farm_public_id}/file",
    response_model=MessageResponse,
)
async def delete_farm_file(
    farm_public_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    service = _get_farm_service(db)

    await service.delete_farm_file(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    return MessageResponse(
        message="Farm file deleted successfully."
    )