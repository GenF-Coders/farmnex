from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.order_dispute_repository import OrderDisputeRepository
from app.schemas.order_dispute_schema import OrderDisputeCreate, OrderDisputeUpdate, OrderDisputeResponse
from app.services.order_dispute_service import OrderDisputeService

router = APIRouter(prefix="/order-disputes", tags=["OrderDispute"])

def _service(db: AsyncSession) -> OrderDisputeService:
    return OrderDisputeService(OrderDisputeRepository(db))

@router.post("", response_model=OrderDisputeResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: OrderDisputeCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> OrderDisputeResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return OrderDisputeResponse.model_validate(entity)

@router.get("", response_model=list[OrderDisputeResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[OrderDisputeResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [OrderDisputeResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=OrderDisputeResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> OrderDisputeResponse:
    entity = await _service(db).get(public_id)
    return OrderDisputeResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=OrderDisputeResponse)
async def update(public_id: UUID, payload: OrderDisputeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> OrderDisputeResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return OrderDisputeResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
