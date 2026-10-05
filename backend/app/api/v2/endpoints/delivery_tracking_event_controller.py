from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.delivery_tracking_event_repository import DeliveryTrackingEventRepository
from app.schemas.delivery_tracking_event_schema import DeliveryTrackingEventCreate, DeliveryTrackingEventUpdate, DeliveryTrackingEventResponse
from app.services.delivery_tracking_event_service import DeliveryTrackingEventService

router = APIRouter(prefix="/delivery-tracking-events", tags=["DeliveryTrackingEvent"])

def _service(db: AsyncSession) -> DeliveryTrackingEventService:
    return DeliveryTrackingEventService(DeliveryTrackingEventRepository(db))

@router.post("", response_model=DeliveryTrackingEventResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: DeliveryTrackingEventCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryTrackingEventResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return DeliveryTrackingEventResponse.model_validate(entity)

@router.get("", response_model=list[DeliveryTrackingEventResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[DeliveryTrackingEventResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [DeliveryTrackingEventResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=DeliveryTrackingEventResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryTrackingEventResponse:
    entity = await _service(db).get(public_id)
    return DeliveryTrackingEventResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=DeliveryTrackingEventResponse)
async def update(public_id: UUID, payload: DeliveryTrackingEventUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryTrackingEventResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return DeliveryTrackingEventResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
