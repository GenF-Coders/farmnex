from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.crop_type_repository import CropTypeRepository
from app.schemas.crop_type_schema import CropTypeCreate, CropTypeResponse, CropTypeUpdate
from app.services.crop_type_service import CropTypeService

router = APIRouter(prefix="/crop-types", tags=["CropType"])

_admin = require_roles("ADMIN", "SUPER_ADMIN")


def get_crop_type_service(db: AsyncSession = Depends(get_db)) -> CropTypeService:
    return CropTypeService(CropTypeRepository(db))


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("", response_model=CropTypeResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: CropTypeCreate,
    current_user: User = Depends(_admin),
    service: CropTypeService = Depends(get_crop_type_service),
) -> CropTypeResponse:
    try:
        return CropTypeResponse.model_validate(await service.create(payload.model_dump(exclude_unset=True), current_user))
    except AppException as exc:
        _raise_http(exc)


@router.get("", response_model=list[CropTypeResponse])
async def list_all(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: CropTypeService = Depends(get_crop_type_service),
) -> list[CropTypeResponse]:
    try:
        entities, _ = await service.list(offset, limit, current_user=current_user)
        return [CropTypeResponse.model_validate(entity) for entity in entities]
    except AppException as exc:
        _raise_http(exc)


@router.get("/{public_id}", response_model=CropTypeResponse)
async def get_one(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: CropTypeService = Depends(get_crop_type_service),
) -> CropTypeResponse:
    try:
        return CropTypeResponse.model_validate(await service.get(public_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{public_id}", response_model=CropTypeResponse)
async def update(
    public_id: UUID,
    payload: CropTypeUpdate,
    current_user: User = Depends(_admin),
    service: CropTypeService = Depends(get_crop_type_service),
) -> CropTypeResponse:
    try:
        entity = await service.update(public_id, payload.model_dump(exclude_unset=True), current_user)
        return CropTypeResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    public_id: UUID,
    current_user: User = Depends(_admin),
    service: CropTypeService = Depends(get_crop_type_service),
) -> None:
    """Retires the crop type (is_active=false); it is not removed."""
    try:
        await service.delete(public_id, current_user)
    except AppException as exc:
        _raise_http(exc)
