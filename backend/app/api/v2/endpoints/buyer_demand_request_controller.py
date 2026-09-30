from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.buyer_demand_request_repository import BuyerDemandRequestRepository
from app.schemas.buyer_demand_request_schema import (
    BuyerDemandRequestCreate,
    BuyerDemandRequestResponse,
    BuyerDemandRequestUpdate,
)
from app.services.buyer_demand_request_service import BuyerDemandRequestService

router = APIRouter(prefix="/buyer-demand-requests", tags=["BuyerDemandRequest"])


def get_demand_service(db: AsyncSession = Depends(get_db)) -> BuyerDemandRequestService:
    return BuyerDemandRequestService(BuyerDemandRequestRepository(db))


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("", response_model=BuyerDemandRequestResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: BuyerDemandRequestCreate,
    current_user: User = Depends(require_roles("BUYER")),
    service: BuyerDemandRequestService = Depends(get_demand_service),
) -> BuyerDemandRequestResponse:
    try:
        entity = await service.create(payload.model_dump(exclude_unset=True), current_user)
        return BuyerDemandRequestResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.get("", response_model=list[BuyerDemandRequestResponse])
async def list_all(
    mine: bool = Query(False, description="Only my own requests (any status)."),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: BuyerDemandRequestService = Depends(get_demand_service),
) -> list[BuyerDemandRequestResponse]:
    try:
        entities, _ = await service.list(offset, limit, current_user=current_user, only_mine=mine)
        return [BuyerDemandRequestResponse.model_validate(entity) for entity in entities]
    except AppException as exc:
        _raise_http(exc)


@router.get("/{public_id}", response_model=BuyerDemandRequestResponse)
async def get_one(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BuyerDemandRequestService = Depends(get_demand_service),
) -> BuyerDemandRequestResponse:
    try:
        return BuyerDemandRequestResponse.model_validate(await service.get(public_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{public_id}", response_model=BuyerDemandRequestResponse)
async def update(
    public_id: UUID,
    payload: BuyerDemandRequestUpdate,
    current_user: User = Depends(get_current_user),
    service: BuyerDemandRequestService = Depends(get_demand_service),
) -> BuyerDemandRequestResponse:
    try:
        entity = await service.update(public_id, payload.model_dump(exclude_unset=True), current_user)
        return BuyerDemandRequestResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: BuyerDemandRequestService = Depends(get_demand_service),
) -> None:
    try:
        await service.delete(public_id, current_user)
    except AppException as exc:
        _raise_http(exc)
