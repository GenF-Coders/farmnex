from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.core.exceptions import NotFoundError, ValidationError
from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, repository: NotificationRepository) -> None:
        self.repository = repository

    async def get(self, public_id: UUID, current_user: User) -> Notification:
        entity = await self.repository.get_owned_by_public_id(public_id, current_user.id)
        if entity is None:
            raise NotFoundError("Notification not found.")
        return entity

    async def list(
        self, offset: int = 0, limit: int = 100, *, current_user: User | None = None
    ) -> tuple[list[Notification], int]:
        """Your own notifications. Without `current_user` it returns every row: that path exists only because
        `me_service` (the dashboard) still calls it that way and filters afterwards; no route uses it."""
        if offset < 0:
            raise ValidationError("Offset cannot be negative.")
        if limit < 1 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")
        if current_user is None:
            return await self.repository.list_all(offset=offset, limit=limit), await self.repository.count_all()
        return (
            await self.repository.list_owned(user_id=current_user.id, offset=offset, limit=limit),
            await self.repository.count_owned(user_id=current_user.id),
        )

    async def set_read(self, public_id: UUID, is_read: bool, current_user: User) -> Notification:
        entity = await self.get(public_id, current_user)
        return await self.repository.update(
            entity, is_read=is_read, read_at=datetime.now(timezone.utc) if is_read else None
        )

    async def delete(self, public_id: UUID, current_user: User) -> None:
        await self.repository.delete(await self.get(public_id, current_user))
