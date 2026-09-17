from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.ai_prediction_repository import AIPredictionRepository
from app.schemas.ai_prediction_schema import AIPredictionCreate, AIPredictionUpdate, AIPredictionResponse
from app.services.ai_prediction_service import AIPredictionService

router = APIRouter(prefix="/ai-predictions", tags=["AIPrediction"])

def _service(db: AsyncSession) -> AIPredictionService:
    return AIPredictionService(AIPredictionRepository(db))

@router.post("", response_model=AIPredictionResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: AIPredictionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AIPredictionResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return AIPredictionResponse.model_validate(entity)

@router.get("", response_model=list[AIPredictionResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[AIPredictionResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [AIPredictionResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=AIPredictionResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AIPredictionResponse:
    entity = await _service(db).get(public_id)
    return AIPredictionResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=AIPredictionResponse)
async def update(public_id: UUID, payload: AIPredictionUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AIPredictionResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return AIPredictionResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
