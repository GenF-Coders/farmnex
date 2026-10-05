from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, entity_id: int) -> AuditLog | None:
        result = await self.db.execute(select(AuditLog).where(AuditLog.id == entity_id))
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> AuditLog | None:
        result = await self.db.execute(select(AuditLog).where(AuditLog.public_id == public_id))
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[AuditLog]:
        result = await self.db.execute(select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def count(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(AuditLog))
        return int(result.scalar_one())

    async def create(self, **values: Any) -> AuditLog:
        entity = AuditLog(**values)
        self.db.add(entity)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def update(self, entity: AuditLog, **values: Any) -> AuditLog:
        for field, value in values.items():
            if hasattr(entity, field):
                setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: AuditLog) -> None:
        await self.db.delete(entity)
        await self.db.flush()
