from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.review_repository import ReviewRepository
from app.schemas.review_schema import ReviewCreate, ReviewUpdate, ReviewResponse
from app.services.review_service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Review"])

def _service(db: AsyncSession) -> ReviewService:
    return ReviewService(ReviewRepository(db))

@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: ReviewCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ReviewResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return ReviewResponse.model_validate(entity)

@router.get("", response_model=list[ReviewResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ReviewResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [ReviewResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=ReviewResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ReviewResponse:
    entity = await _service(db).get(public_id)
    return ReviewResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=ReviewResponse)
async def update(public_id: UUID, payload: ReviewUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> ReviewResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return ReviewResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
