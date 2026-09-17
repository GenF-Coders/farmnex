from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.buyer_demand_request_repository import BuyerDemandRequestRepository
from app.schemas.buyer_demand_request_schema import BuyerDemandRequestCreate, BuyerDemandRequestUpdate, BuyerDemandRequestResponse
from app.services.buyer_demand_request_service import BuyerDemandRequestService

router = APIRouter(prefix="/buyer-demand-requests", tags=["BuyerDemandRequest"])

def _service(db: AsyncSession) -> BuyerDemandRequestService:
    return BuyerDemandRequestService(BuyerDemandRequestRepository(db))

@router.post("", response_model=BuyerDemandRequestResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: BuyerDemandRequestCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> BuyerDemandRequestResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return BuyerDemandRequestResponse.model_validate(entity)

@router.get("", response_model=list[BuyerDemandRequestResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[BuyerDemandRequestResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [BuyerDemandRequestResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=BuyerDemandRequestResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> BuyerDemandRequestResponse:
    entity = await _service(db).get(public_id)
    return BuyerDemandRequestResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=BuyerDemandRequestResponse)
async def update(public_id: UUID, payload: BuyerDemandRequestUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> BuyerDemandRequestResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return BuyerDemandRequestResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
