from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FarmCreateRequest(BaseModel):
    farm_name: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    address_public_id: UUID

    @field_validator("farm_name", "description")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class FarmUpdateRequest(BaseModel):
    farm_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    address_public_id: UUID | None = None

    @field_validator("farm_name", "description")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    user_id: int
    address_id: int

    farm_name: str
    description: str | None

    created_at: datetime
    updated_at: datetime


class FarmListResponse(BaseModel):
    items: list[FarmResponse]
    total: int
    offset: int
    limit: int