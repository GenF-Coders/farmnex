from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification_schema import NotificationResponse, NotificationUpdate
from app.services.notification_service import NotificationService

# There is no public POST: notifications are created by the server (FIX_PLAN F1, "server only").
router = APIRouter(prefix="/notifications", tags=["Notification"])


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("", response_model=list[NotificationResponse])
async def list_all(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> list[NotificationResponse]:
    try:
        entities, _ = await service.list(offset, limit, current_user=current_user)
        return [NotificationResponse.model_validate(entity) for entity in entities]
    except AppException as exc:
        _raise_http(exc)


@router.get("/{public_id}", response_model=NotificationResponse)
async def get_one(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    try:
        return NotificationResponse.model_validate(await service.get(public_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{public_id}", response_model=NotificationResponse)
async def mark_read(
    public_id: UUID,
    payload: NotificationUpdate,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationResponse:
    try:
        entity = await service.set_read(public_id, payload.is_read, current_user)
        return NotificationResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> None:
    try:
        await service.delete(public_id, current_user)
    except AppException as exc:
        _raise_http(exc)
