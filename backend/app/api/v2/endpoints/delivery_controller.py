from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.delivery_repository import DeliveryRepository
from app.schemas.delivery_schema import DeliveryCreate, DeliveryUpdate, DeliveryResponse
from app.services.delivery_service import DeliveryService

router = APIRouter(prefix="/deliverys", tags=["Delivery"])

def _service(db: AsyncSession) -> DeliveryService:
    return DeliveryService(DeliveryRepository(db))

@router.post("", response_model=DeliveryResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: DeliveryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return DeliveryResponse.model_validate(entity)

@router.get("", response_model=list[DeliveryResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[DeliveryResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [DeliveryResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=DeliveryResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryResponse:
    entity = await _service(db).get(public_id)
    return DeliveryResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=DeliveryResponse)
async def update(public_id: UUID, payload: DeliveryUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return DeliveryResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
