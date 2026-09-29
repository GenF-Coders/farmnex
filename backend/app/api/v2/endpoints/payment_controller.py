from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payment_schema import PaymentCreate, PaymentUpdate, PaymentResponse
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payment"])

def _service(db: AsyncSession) -> PaymentService:
    return PaymentService(PaymentRepository(db))

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: PaymentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> PaymentResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return PaymentResponse.model_validate(entity)

@router.get("", response_model=list[PaymentResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[PaymentResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [PaymentResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=PaymentResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> PaymentResponse:
    entity = await _service(db).get(public_id)
    return PaymentResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=PaymentResponse)
async def update(public_id: UUID, payload: PaymentUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> PaymentResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return PaymentResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
