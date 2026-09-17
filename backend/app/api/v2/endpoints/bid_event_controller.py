from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.bid_event_repository import BidEventRepository
from app.schemas.bid_event_schema import BidEventCreate, BidEventUpdate, BidEventResponse
from app.services.bid_event_service import BidEventService

router = APIRouter(prefix="/bid-events", tags=["BidEvent"])

def _service(db: AsyncSession) -> BidEventService:
    return BidEventService(BidEventRepository(db))

@router.post("", response_model=BidEventResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: BidEventCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> BidEventResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return BidEventResponse.model_validate(entity)

@router.get("", response_model=list[BidEventResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[BidEventResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [BidEventResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=BidEventResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> BidEventResponse:
    entity = await _service(db).get(public_id)
    return BidEventResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=BidEventResponse)
async def update(public_id: UUID, payload: BidEventUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> BidEventResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return BidEventResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
