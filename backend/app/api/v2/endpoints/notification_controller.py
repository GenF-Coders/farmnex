from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification_schema import NotificationCreate, NotificationUpdate, NotificationResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notification"])

def _service(db: AsyncSession) -> NotificationService:
    return NotificationService(NotificationRepository(db))

@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: NotificationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> NotificationResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return NotificationResponse.model_validate(entity)

@router.get("", response_model=list[NotificationResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[NotificationResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [NotificationResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=NotificationResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> NotificationResponse:
    entity = await _service(db).get(public_id)
    return NotificationResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=NotificationResponse)
async def update(public_id: UUID, payload: NotificationUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> NotificationResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return NotificationResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
