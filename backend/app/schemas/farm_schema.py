from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FarmCreateRequest(BaseModel):
    farm_name: str = Field(
        min_length=1,
        max_length=150,
    )

    description: str | None = None

    address_line_1: str = Field(
        min_length=1,
        max_length=255,
    )

    address_line_2: str | None = Field(
        default=None,
        max_length=255,
    )

    landmark: str | None = Field(
        default=None,
        max_length=255,
    )

    village: str | None = Field(
        default=None,
        max_length=150,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    district: str | None = Field(
        default=None,
        max_length=150,
    )

    state: str = Field(
        min_length=1,
        max_length=150,
    )

    postal_code: str = Field(
        min_length=1,
        max_length=20,
    )

    country: str = Field(
        default="India",
        min_length=1,
        max_length=100,
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=-180,
        le=180,
    )


class FarmUpdateRequest(BaseModel):
    farm_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    description: str | None = None

    address_line_1: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    address_line_2: str | None = Field(
        default=None,
        max_length=255,
    )

    landmark: str | None = Field(
        default=None,
        max_length=255,
    )

    village: str | None = Field(
        default=None,
        max_length=150,
    )

    city: str | None = Field(
        default=None,
        max_length=150,
    )

    district: str | None = Field(
        default=None,
        max_length=150,
    )

    state: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    postal_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=20,
    )

    country: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=-90,
        le=90,
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=-180,
        le=180,
    )

    is_active: bool | None = None

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID

    farm_name: str
    description: str | None = None

    address_line_1: str
    address_line_2: str | None = None
    landmark: str | None = None
    village: str | None = None
    city: str
    district: str
    state: str
    postal_code: str
    country: str

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    farm_file_url: str | None = None
    farm_file_content_type: str | None = None

    is_active: bool

    created_at: datetime
    updated_at: datetime


class FarmListResponse(BaseModel):
    items: list[FarmResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class FarmFileUrlResponse(BaseModel):
    farm_file_url: str
    farm_file_content_type: str


class MessageResponse(BaseModel):
    message: str