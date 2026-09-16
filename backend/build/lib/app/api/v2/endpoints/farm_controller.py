from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies.current_user import get_current_user
from app.models.user import User
from app.schemas.farm_schema import (
    FarmCreateRequest,
    FarmFileUrlResponse,
    FarmListResponse,
    FarmResponse,
    FarmUpdateRequest,
    MessageResponse,
)
from app.services.farm_service import FarmService
from app.api.dependencies.services import get_farm_service


router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_farm(
    payload: FarmCreateRequest,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    farm = await service.create_farm(
        user_id=current_user.id,
        farm_data=payload.model_dump(),
    )

    response_data = await service.build_farm_response_data(farm)

    return FarmResponse.model_validate(response_data)


@router.get(
    "",
    response_model=FarmListResponse,
)
async def list_farms(
    offset: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    farms, total = await service.list_farms(
        user_id=current_user.id,
        offset=offset,
        limit=limit,
    )

    items = []

    for farm in farms:
        response_data = await service.build_farm_response_data(
            farm
        )

        items.append(
            FarmResponse.model_validate(response_data)
        )

    return FarmListResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{farm_public_id}",
    response_model=FarmResponse,
)
async def get_farm(
    farm_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    farm = await service.get_farm(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    response_data = await service.build_farm_response_data(
        farm
    )

    return FarmResponse.model_validate(response_data)


@router.patch(
    "/{farm_public_id}",
    response_model=FarmResponse,
)
async def update_farm(
    farm_public_id: UUID,
    payload: FarmUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    farm = await service.update_farm(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
        farm_data=payload.model_dump(
            exclude_unset=True
        ),
    )

    response_data = await service.build_farm_response_data(
        farm
    )

    return FarmResponse.model_validate(response_data)


@router.delete(
    "/{farm_public_id}",
    response_model=MessageResponse,
)
async def delete_farm(
    farm_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    await service.delete_farm(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    return MessageResponse(
        message="Farm deleted successfully."
    )


# ------------------------------------------------------------------
# Farm file
# ------------------------------------------------------------------

@router.post(
    "/{farm_public_id}/file",
    response_model=FarmFileUrlResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_or_replace_farm_file(
    farm_public_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    file_bytes = await file.read()

    url, content_type = await service.upload_farm_file(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
        file_bytes=file_bytes,
        content_type=file.content_type
        or "application/octet-stream",
        filename=file.filename,
    )

    return FarmFileUrlResponse(
        farm_file_url=url,
        farm_file_content_type=content_type,
    )


@router.get(
    "/{farm_public_id}/file",
    response_model=FarmFileUrlResponse,
)
async def get_farm_file_url(
    farm_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    url, content_type = await service.get_farm_file_url(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    return FarmFileUrlResponse(
        farm_file_url=url,
        farm_file_content_type=content_type,
    )


@router.get(
    "/{farm_public_id}/file/download",
)
async def download_farm_file(
    farm_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    from fastapi.responses import Response

    file_bytes, content_type = await service.download_farm_file(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    return Response(
        content=file_bytes,
        media_type=content_type,
    )


@router.delete(
    "/{farm_public_id}/file",
    response_model=MessageResponse,
)
async def delete_farm_file(
    farm_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
):
    await service.delete_farm_file(
        user_id=current_user.id,
        farm_public_id=farm_public_id,
    )

    return MessageResponse(
        message="Farm file deleted successfully."
    )