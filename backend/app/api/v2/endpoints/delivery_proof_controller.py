from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.delivery_proof_repository import DeliveryProofRepository
from app.schemas.delivery_proof_schema import DeliveryProofCreate, DeliveryProofUpdate, DeliveryProofResponse
from app.services.delivery_proof_service import DeliveryProofService

router = APIRouter(prefix="/delivery-proofs", tags=["DeliveryProof"])

def _service(db: AsyncSession) -> DeliveryProofService:
    return DeliveryProofService(DeliveryProofRepository(db))

@router.post("", response_model=DeliveryProofResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: DeliveryProofCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryProofResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return DeliveryProofResponse.model_validate(entity)

@router.get("", response_model=list[DeliveryProofResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[DeliveryProofResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [DeliveryProofResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=DeliveryProofResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryProofResponse:
    entity = await _service(db).get(public_id)
    return DeliveryProofResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=DeliveryProofResponse)
async def update(public_id: UUID, payload: DeliveryProofUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> DeliveryProofResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return DeliveryProofResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
