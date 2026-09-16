from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FarmCreateRequest(BaseModel):
    farm_name: str = Field(min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    village: str | None = Field(default=None, max_length=150)
    city: str = Field(min_length=1, max_length=150)
    district: str | None = Field(default=None, max_length=150)
    state: str = Field(min_length=1, max_length=150)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(default="India", min_length=1, max_length=100)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    @field_validator("farm_name", "description", "address_line_1", "address_line_2", "landmark", "village", "city", "district", "state", "postal_code", "country")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None and value.strip() else None


class FarmUpdateRequest(BaseModel):
    farm_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=5000)
    address_line_1: str | None = Field(default=None, min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    village: str | None = Field(default=None, max_length=150)
    city: str | None = Field(default=None, min_length=1, max_length=150)
    district: str | None = Field(default=None, max_length=150)
    state: str | None = Field(default=None, min_length=1, max_length=150)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)
    is_active: bool | None = None

    @field_validator("farm_name", "description", "address_line_1", "address_line_2", "landmark", "village", "city", "district", "state", "postal_code", "country")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None and value.strip() else None


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID
    farm_name: str
    description: str | None
    address_line_1: str
    address_line_2: str | None
    landmark: str | None
    village: str | None
    city: str
    district: str | None
    state: str
    postal_code: str
    country: str
    latitude: Decimal | None
    longitude: Decimal | None
    is_active: bool
    farm_file_path: str | None
    farm_file_content_type: str | None
    created_at: datetime
    updated_at: datetime


class FarmListResponse(BaseModel):
    items: list[FarmResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class FarmFileResponse(BaseModel):
    farm: FarmResponse
    farm_file_url: str


class FarmFileUrlResponse(BaseModel):
    farm_file_url: str


class MessageResponse(BaseModel):
    message: str
