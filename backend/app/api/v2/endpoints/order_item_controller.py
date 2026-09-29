from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.order_item_repository import OrderItemRepository
from app.schemas.order_item_schema import OrderItemCreate, OrderItemUpdate, OrderItemResponse
from app.services.order_item_service import OrderItemService

router = APIRouter(prefix="/order-items", tags=["OrderItem"])

def _service(db: AsyncSession) -> OrderItemService:
    return OrderItemService(OrderItemRepository(db))

@router.post("", response_model=OrderItemResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: OrderItemCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> OrderItemResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return OrderItemResponse.model_validate(entity)

@router.get("", response_model=list[OrderItemResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[OrderItemResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [OrderItemResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=OrderItemResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> OrderItemResponse:
    entity = await _service(db).get(public_id)
    return OrderItemResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=OrderItemResponse)
async def update(public_id: UUID, payload: OrderItemUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> OrderItemResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return OrderItemResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
