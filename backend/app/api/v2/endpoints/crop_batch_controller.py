from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.crop_batch_repository import CropBatchRepository
from app.schemas.crop_batch_schema import CropBatchCreate, CropBatchUpdate, CropBatchResponse
from app.services.crop_batch_service import CropBatchService

router = APIRouter(prefix="/crop-batchs", tags=["CropBatch"])

def _service(db: AsyncSession) -> CropBatchService:
    return CropBatchService(CropBatchRepository(db))

@router.post("", response_model=CropBatchResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: CropBatchCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> CropBatchResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return CropBatchResponse.model_validate(entity)

@router.get("", response_model=list[CropBatchResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[CropBatchResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [CropBatchResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=CropBatchResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> CropBatchResponse:
    entity = await _service(db).get(public_id)
    return CropBatchResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=CropBatchResponse)
async def update(public_id: UUID, payload: CropBatchUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> CropBatchResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return CropBatchResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
