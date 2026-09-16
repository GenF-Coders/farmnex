from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AddressCreateRequest(BaseModel):
    """
    Request schema for creating an address.

    user_id is intentionally excluded.
    Ownership always comes from the authenticated user.
    """

    model_config = ConfigDict(extra="ignore")

    address_line_1: str = Field(min_length=1, max_length=255)
    address_line_2: str | None = Field(default=None, max_length=255)
    landmark: str | None = Field(default=None, max_length=255)

    village: str | None = Field(default=None, max_length=150)
    city: str = Field(min_length=1, max_length=150)
    district: str | None = Field(default=None, max_length=150)
    state: str = Field(min_length=1, max_length=150)

    postal_code: str = Field(min_length=3, max_length=20)
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
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class AddressUpdateRequest(BaseModel):
    """
    Partial update schema.

    user_id is intentionally excluded.
    Ownership always comes from the authenticated user.
    """

    model_config = ConfigDict(extra="ignore")

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
    is_active: bool | None = None

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
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class AddressResponse(BaseModel):
    """
    Response schema for a single address.
    """

    model_config = ConfigDict(from_attributes=True)

    public_id: UUID

    address_line_1: str
    address_line_2: str | None = None
    landmark: str | None = None

    village: str | None = None
    city: str
    district: str | None = None
    state: str

    postal_code: str
    country: str

    latitude: Decimal | None = None
    longitude: Decimal | None = None

    is_default: bool
    is_active: bool

    created_at: datetime
    updated_at: datetime


class AddressListResponse(BaseModel):
    """
    Paginated response schema for addresses.

    `items` matches AddressService.list_addresses(), which returns
    (items, total).
    """

    items: list[AddressResponse]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
