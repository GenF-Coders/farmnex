from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_owned_by_public_id(self, public_id: UUID, user_id: int) -> Notification | None:
        result = await self.db.execute(
            select(Notification).where(Notification.public_id == public_id, Notification.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def list_owned(self, *, user_id: int, offset: int, limit: int) -> list[Notification]:
        result = await self.db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_owned(self, *, user_id: int) -> int:
        result = await self.db.execute(select(func.count(Notification.id)).where(Notification.user_id == user_id))
        return int(result.scalar_one())

    async def list_all(self, *, offset: int, limit: int) -> list[Notification]:
        """Every user's rows. Only for the dashboard, which filters them afterwards (STATUS follow-up)."""
        result = await self.db.execute(
            select(Notification).order_by(Notification.created_at.desc(), Notification.id.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        result = await self.db.execute(select(func.count()).select_from(Notification))
        return int(result.scalar_one())

    async def update(self, entity: Notification, **values: Any) -> Notification:
        for field, value in values.items():
            setattr(entity, field, value)
        await self.db.flush()
        await self.db.refresh(entity)
        return entity

    async def delete(self, entity: Notification) -> None:
        await self.db.delete(entity)
        await self.db.flush()
