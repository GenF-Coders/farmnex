from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.waste_record_repository import WasteRecordRepository
from app.schemas.waste_record_schema import WasteRecordCreate, WasteRecordResponse, WasteRecordUpdate
from app.services.waste_record_service import WasteRecordService

router = APIRouter(prefix="/waste-records", tags=["WasteRecord"])


def get_waste_record_service(db: AsyncSession = Depends(get_db)) -> WasteRecordService:
    return WasteRecordService(WasteRecordRepository(db))


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("", response_model=WasteRecordResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: WasteRecordCreate,
    current_user: User = Depends(require_roles("FARMER")),
    service: WasteRecordService = Depends(get_waste_record_service),
) -> WasteRecordResponse:
    try:
        entity = await service.create(payload.model_dump(exclude_unset=True), current_user)
        return WasteRecordResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.get("", response_model=list[WasteRecordResponse])
async def list_all(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: WasteRecordService = Depends(get_waste_record_service),
) -> list[WasteRecordResponse]:
    try:
        entities, _ = await service.list(offset, limit, current_user=current_user)
        return [WasteRecordResponse.model_validate(entity) for entity in entities]
    except AppException as exc:
        _raise_http(exc)


@router.get("/{public_id}", response_model=WasteRecordResponse)
async def get_one(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WasteRecordService = Depends(get_waste_record_service),
) -> WasteRecordResponse:
    try:
        return WasteRecordResponse.model_validate(await service.get(public_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{public_id}", response_model=WasteRecordResponse)
async def update(
    public_id: UUID,
    payload: WasteRecordUpdate,
    current_user: User = Depends(get_current_user),
    service: WasteRecordService = Depends(get_waste_record_service),
) -> WasteRecordResponse:
    try:
        entity = await service.update(public_id, payload.model_dump(exclude_unset=True), current_user)
        return WasteRecordResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: WasteRecordService = Depends(get_waste_record_service),
) -> None:
    try:
        await service.delete(public_id, current_user)
    except AppException as exc:
        _raise_http(exc)
