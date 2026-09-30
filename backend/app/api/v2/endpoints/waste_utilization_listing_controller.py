from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.waste_utilization_listing_repository import WasteUtilizationListingRepository
from app.schemas.waste_utilization_listing_schema import (
    WasteUtilizationListingCreate,
    WasteUtilizationListingResponse,
    WasteUtilizationListingUpdate,
)
from app.services.waste_utilization_listing_service import WasteUtilizationListingService

router = APIRouter(prefix="/waste-utilization-listings", tags=["WasteUtilizationListing"])


def get_waste_listing_service(db: AsyncSession = Depends(get_db)) -> WasteUtilizationListingService:
    return WasteUtilizationListingService(WasteUtilizationListingRepository(db))


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("", response_model=WasteUtilizationListingResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: WasteUtilizationListingCreate,
    current_user: User = Depends(require_roles("FARMER")),
    service: WasteUtilizationListingService = Depends(get_waste_listing_service),
) -> WasteUtilizationListingResponse:
    try:
        entity = await service.create(payload.model_dump(exclude_unset=True), current_user)
        return WasteUtilizationListingResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.get("", response_model=list[WasteUtilizationListingResponse])
async def list_all(
    mine: bool = Query(False, description="Only my own listings (any status)."),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WasteUtilizationListingService = Depends(get_waste_listing_service),
) -> list[WasteUtilizationListingResponse]:
    try:
        entities, _ = await service.list(offset, limit, current_user=current_user, only_mine=mine)
        return [WasteUtilizationListingResponse.model_validate(entity) for entity in entities]
    except AppException as exc:
        _raise_http(exc)


@router.get("/{public_id}", response_model=WasteUtilizationListingResponse)
async def get_one(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WasteUtilizationListingService = Depends(get_waste_listing_service),
) -> WasteUtilizationListingResponse:
    try:
        return WasteUtilizationListingResponse.model_validate(await service.get(public_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{public_id}", response_model=WasteUtilizationListingResponse)
async def update(
    public_id: UUID,
    payload: WasteUtilizationListingUpdate,
    current_user: User = Depends(get_current_user),
    service: WasteUtilizationListingService = Depends(get_waste_listing_service),
) -> WasteUtilizationListingResponse:
    try:
        entity = await service.update(public_id, payload.model_dump(exclude_unset=True), current_user)
        return WasteUtilizationListingResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WasteUtilizationListingService = Depends(get_waste_listing_service),
) -> None:
    try:
        await service.delete(public_id, current_user)
    except AppException as exc:
        _raise_http(exc)
