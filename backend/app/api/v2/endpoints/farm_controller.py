from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.farm import get_farm_service
from app.models.user import User
from app.schemas.farm_schema import (
    FarmCreateRequest,
    FarmListResponse,
    FarmResponse,
    FarmUpdateRequest,
)
from app.services.exceptions import (
    ConflictError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.farm_service import FarmService


router = APIRouter(
    prefix="/farms",
    tags=["Farms"],
)


@router.get(
    "",
    response_model=FarmListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_my_farms(
    offset: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
) -> FarmListResponse:
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


@router.get(
    "/{farm_public_id}",
    response_model=FarmResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_farm(
    farm_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
) -> FarmResponse:
    try:
        return await service.get_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=FarmResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_my_farm(
    payload: FarmCreateRequest,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
) -> FarmResponse:
    try:
        return await service.create_farm(
            current_user=current_user,
            data=payload.model_dump(exclude_unset=True),
        )

    except ResourceAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{farm_public_id}",
    response_model=FarmResponse,
    status_code=status.HTTP_200_OK,
)
async def update_my_farm(
    farm_public_id: UUID,
    payload: FarmUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
) -> FarmResponse:
    try:
        return await service.update_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
            data=payload.model_dump(exclude_unset=True),
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ResourceAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{farm_public_id}/address/{address_public_id}",
    response_model=FarmResponse,
    status_code=status.HTTP_200_OK,
)
async def change_farm_address(
    farm_public_id: UUID,
    address_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
) -> FarmResponse:
    try:
        return await service.change_farm_address(
            current_user=current_user,
            farm_public_id=farm_public_id,
            address_public_id=address_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{farm_public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_my_farm(
    farm_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmService = Depends(get_farm_service),
) -> None:
    try:
        await service.delete_farm(
            current_user=current_user,
            farm_public_id=farm_public_id,
        )

    except ResourceNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc