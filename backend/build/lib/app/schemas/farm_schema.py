from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FarmCreateRequest(BaseModel):
    farm_name: str = Field(min_length=1, max_length=255)
    description: str | None = None

    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    village: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str = Field(default="India", max_length=100)

    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)


class FarmUpdateRequest(BaseModel):
    farm_name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None

    address_line_1: str | None = Field(default=None, min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)
    village: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    district: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)

    latitude: Decimal | None = Field(default=None, ge=-90, le=90)
    longitude: Decimal | None = Field(default=None, ge=-180, le=180)

    is_active: bool | None = None


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    farm_name: str
    description: str | None

    address_line_1: str
    address_line_2: str | None
    landmark: str | None
    village: str | None
    city: str | None
    district: str | None
    state: str | None
    postal_code: str | None
    country: str

    latitude: Decimal | None
    longitude: Decimal | None

    is_active: bool

    # Storage path is intentionally NOT exposed.
    farm_file_url: str | None = None
    farm_file_content_type: str | None = None

    created_at: datetime
    updated_at: datetime


class FarmListResponse(BaseModel):
    items: list[FarmResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class FarmFileUrlResponse(BaseModel):
    farm_file_url: str
    farm_file_content_type: str | None = None


class MessageResponse(BaseModel):
    message: str