from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.farm_crop_repository import FarmCropRepository
from app.schemas.farm_crop_schema import FarmCropCreate, FarmCropUpdate, FarmCropResponse
from app.services.farm_crop_service import FarmCropService

router = APIRouter(prefix="/farm-crops", tags=["FarmCrop"])

def _service(db: AsyncSession) -> FarmCropService:
    return FarmCropService(FarmCropRepository(db))

@router.post("", response_model=FarmCropResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: FarmCropCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> FarmCropResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return FarmCropResponse.model_validate(entity)

@router.get("", response_model=list[FarmCropResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[FarmCropResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [FarmCropResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=FarmCropResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> FarmCropResponse:
    entity = await _service(db).get(public_id)
    return FarmCropResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=FarmCropResponse)
async def update(public_id: UUID, payload: FarmCropUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> FarmCropResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return FarmCropResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
