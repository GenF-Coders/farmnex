from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.schemas.ai_recommendation_schema import AIRecommendationCreate, AIRecommendationUpdate, AIRecommendationResponse
from app.services.ai_recommendation_service import AIRecommendationService

router = APIRouter(prefix="/ai-recommendations", tags=["AIRecommendation"])

def _service(db: AsyncSession) -> AIRecommendationService:
    return AIRecommendationService(AIRecommendationRepository(db))

@router.post("", response_model=AIRecommendationResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: AIRecommendationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AIRecommendationResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return AIRecommendationResponse.model_validate(entity)

@router.get("", response_model=list[AIRecommendationResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[AIRecommendationResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [AIRecommendationResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=AIRecommendationResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AIRecommendationResponse:
    entity = await _service(db).get(public_id)
    return AIRecommendationResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=AIRecommendationResponse)
async def update(public_id: UUID, payload: AIRecommendationUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AIRecommendationResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return AIRecommendationResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
