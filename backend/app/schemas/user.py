from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    phone_number: str
    phone_verified_at: datetime | None
    role: RoleResponse
    account_status: str
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None
