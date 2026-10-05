from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.farm_crop_activity_repository import FarmCropActivityRepository
from app.schemas.farm_crop_activity_schema import FarmCropActivityCreate, FarmCropActivityUpdate, FarmCropActivityResponse
from app.services.farm_crop_activity_service import FarmCropActivityService

router = APIRouter(prefix="/farm-crop-activitys", tags=["FarmCropActivity"])

def _service(db: AsyncSession) -> FarmCropActivityService:
    return FarmCropActivityService(FarmCropActivityRepository(db))

@router.post("", response_model=FarmCropActivityResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: FarmCropActivityCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> FarmCropActivityResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return FarmCropActivityResponse.model_validate(entity)

@router.get("", response_model=list[FarmCropActivityResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[FarmCropActivityResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [FarmCropActivityResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=FarmCropActivityResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> FarmCropActivityResponse:
    entity = await _service(db).get(public_id)
    return FarmCropActivityResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=FarmCropActivityResponse)
async def update(public_id: UUID, payload: FarmCropActivityUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> FarmCropActivityResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return FarmCropActivityResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
