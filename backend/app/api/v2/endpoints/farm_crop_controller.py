from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.farm_crop_repository import FarmCropRepository
from app.schemas.farm_crop_schema import FarmCropCreate, FarmCropResponse, FarmCropUpdate
from app.services.farm_crop_service import FarmCropService

router = APIRouter(prefix="/farm-crops", tags=["FarmCrop"])


def get_farm_crop_service(db: AsyncSession = Depends(get_db)) -> FarmCropService:
    return FarmCropService(FarmCropRepository(db))


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("", response_model=FarmCropResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: FarmCropCreate,
    current_user: User = Depends(get_current_user),
    service: FarmCropService = Depends(get_farm_crop_service),
) -> FarmCropResponse:
    try:
        entity = await service.create(payload.model_dump(exclude_unset=True), current_user)
        return FarmCropResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.get("", response_model=list[FarmCropResponse])
async def list_all(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: FarmCropService = Depends(get_farm_crop_service),
) -> list[FarmCropResponse]:
    try:
        entities, _ = await service.list(current_user=current_user, offset=offset, limit=limit)
        return [FarmCropResponse.model_validate(entity) for entity in entities]
    except AppException as exc:
        _raise_http(exc)


@router.get("/{public_id}", response_model=FarmCropResponse)
async def get_one(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmCropService = Depends(get_farm_crop_service),
) -> FarmCropResponse:
    try:
        return FarmCropResponse.model_validate(await service.get(public_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{public_id}", response_model=FarmCropResponse)
async def update(
    public_id: UUID,
    payload: FarmCropUpdate,
    current_user: User = Depends(get_current_user),
    service: FarmCropService = Depends(get_farm_crop_service),
) -> FarmCropResponse:
    try:
        entity = await service.update(public_id, payload.model_dump(exclude_unset=True), current_user)
        return FarmCropResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FarmCropService = Depends(get_farm_crop_service),
) -> None:
    try:
        await service.delete(public_id, current_user)
    except AppException as exc:
        _raise_http(exc)
