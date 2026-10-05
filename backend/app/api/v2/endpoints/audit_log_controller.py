from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log_schema import AuditLogCreate, AuditLogUpdate, AuditLogResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["AuditLog"])

def _service(db: AsyncSession) -> AuditLogService:
    return AuditLogService(AuditLogRepository(db))

@router.post("", response_model=AuditLogResponse, status_code=status.HTTP_201_CREATED)
async def create(payload: AuditLogCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AuditLogResponse:
    # Ownership/authorization rules beyond the direct actor field belong in the domain service.
    entity = await _service(db).create(payload.model_dump(exclude_unset=True))
    return AuditLogResponse.model_validate(entity)

@router.get("", response_model=list[AuditLogResponse])
async def list_all(offset: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[AuditLogResponse]:
    entities, _ = await _service(db).list(offset, limit)
    return [AuditLogResponse.model_validate(x) for x in entities]

@router.get("/{public_id}", response_model=AuditLogResponse)
async def get_one(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AuditLogResponse:
    entity = await _service(db).get(public_id)
    return AuditLogResponse.model_validate(entity)

@router.patch("/{public_id}", response_model=AuditLogResponse)
async def update(public_id: UUID, payload: AuditLogUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> AuditLogResponse:
    entity = await _service(db).update(public_id, payload.model_dump(exclude_unset=True))
    return AuditLogResponse.model_validate(entity)

@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(public_id: UUID, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    await _service(db).delete(public_id)
