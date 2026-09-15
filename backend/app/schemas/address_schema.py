from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressCreateRequest(BaseModel):
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

    city: str = Field(
        min_length=1,
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
        min_length=3,
        max_length=20,
    )

    country: str = Field(
        default="India",
        min_length=1,
        max_length=100,
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )

    is_default: bool = False

    @field_validator(
        "address_line_1",
        "address_line_2",
        "landmark",
        "village",
        "city",
        "district",
        "state",
        "postal_code",
        "country",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class AddressUpdateRequest(BaseModel):
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
        min_length=1,
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
        min_length=3,
        max_length=20,
    )

    country: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    latitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )

    longitude: Decimal | None = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )

    is_default: bool | None = None

    @field_validator(
        "address_line_1",
        "address_line_2",
        "landmark",
        "village",
        "city",
        "district",
        "state",
        "postal_code",
        "country",
    )
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class AddressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    user_id: int

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

    is_default: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime


class AddressListResponse(BaseModel):
    items: list[AddressResponse]
    total: int
    offset: int
    limit: int