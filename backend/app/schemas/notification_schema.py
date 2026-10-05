from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationUpdate(BaseModel):
    """The only thing a user may change on a notification: read or unread. The server sets `read_at`.

    There is no create schema: notifications are created by the server (for example when a bid is placed)."""

    is_read: bool


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    title: str
    message: str
    notification_type: str
    data: dict | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
