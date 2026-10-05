from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CropTypeCreate(BaseModel):
    """Admin only. A new crop type starts active."""

    name: str = Field(min_length=1, max_length=150)
    scientific_name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    default_unit: str = Field(min_length=1, max_length=30)


class CropTypeUpdate(BaseModel):
    """Admin only. `is_active=false` is how a crop type is retired (delete does the same)."""

    name: str | None = Field(default=None, min_length=1, max_length=150)
    scientific_name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    default_unit: str | None = Field(default=None, min_length=1, max_length=30)
    is_active: bool | None = None


class CropTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    scientific_name: str | None = None
    description: str | None = None
    category: str | None = None
    default_unit: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
