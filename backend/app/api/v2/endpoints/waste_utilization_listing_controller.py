from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.waste_utilization_listing_repository import WasteUtilizationListingRepository
from app.schemas.waste_utilization_listing_schema import WasteUtilizationListingCreate, WasteUtilizationListingUpdate, WasteUtilizationListingResponse
from app.services.waste_utilization_listing_service import WasteUtilizationListingService

router = APIRouter(prefix="/waste-utilization-listings", tags=["WasteUtilizationListing"])

def _service(db: AsyncSession) -> WasteUtilizationListingService:
    return WasteUtilizationListingService(WasteUtilizationListingRepository(db))

@router.post("", response_model=WasteUtilizationListingResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: WasteUtilizationListingCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> WasteUtilizationListingResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return WasteUtilizationListingResponse.model_validate(entity)

@router.get("", response_model=list[WasteUtilizationListingResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[WasteUtilizationListingResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [WasteUtilizationListingResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=WasteUtilizationListingResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> WasteUtilizationListingResponse:
    entity = await _service(db).get(public_id)
    return WasteUtilizationListingResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=WasteUtilizationListingResponse)
async def update(public_id: UUID, payload: WasteUtilizationListingUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> WasteUtilizationListingResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return WasteUtilizationListingResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
