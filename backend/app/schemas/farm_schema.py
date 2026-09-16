from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# COMMON CONFIG
# ============================================================


class FarmSchemaBase(BaseModel):
    """
    Common Pydantic configuration for Farm schemas.
    """

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        extra="forbid",
    )


# ============================================================
# CREATE
# ============================================================


class FarmCreateRequest(FarmSchemaBase):
    """
    Request payload for creating a farm.

    Address information is stored directly on the Farm entity.
    """

    farm_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the farm.",
    )

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional description of the farm.",
    )

    address_line_1: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Primary address line.",
    )

    address_line_2: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Secondary address line.",
    )

    landmark: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Nearby landmark.",
    )

    village: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Village or locality.",
    )

    city: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="City or town.",
    )

    district: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="District.",
    )

    state: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="State.",
    )

    postal_code: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Postal or PIN code.",
    )

    country: str = Field(
        default="India",
        min_length=1,
        max_length=100,
        description="Country.",
    )

    latitude: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
        description="Latitude.",
    )

    longitude: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
        description="Longitude.",
    )

    @field_validator("farm_name")
    @classmethod
    def validate_farm_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Farm name cannot be empty."
            )

        return value

    @field_validator(
        "address_line_1",
        "village",
        "city",
        "district",
        "state",
        "postal_code",
        "country",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty."
            )

        return value


# ============================================================
# UPDATE
# ============================================================


class FarmUpdateRequest(FarmSchemaBase):
    """
    Partial update payload for an existing farm.

    Every field is optional because the controller uses
    model_dump(exclude_unset=True).
    """

    farm_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=2000,
    )

    address_line_1: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    address_line_2: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    landmark: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    village: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    city: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    district: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    state: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    postal_code: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=20,
    )

    country: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    latitude: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-90"),
        le=Decimal("90"),
    )

    longitude: Optional[Decimal] = Field(
        default=None,
        ge=Decimal("-180"),
        le=Decimal("180"),
    )

    @field_validator("farm_name")
    @classmethod
    def validate_farm_name(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Farm name cannot be empty."
            )

        return value

    @field_validator(
        "address_line_1",
        "village",
        "city",
        "district",
        "state",
        "postal_code",
        "country",
    )
    @classmethod
    def validate_text(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty."
            )

        return value


# ============================================================
# FARM RESPONSE
# ============================================================


class FarmResponse(FarmSchemaBase):
    """
    Public Farm representation returned by the API.
    """

    public_id: UUID

    farm_name: str

    description: Optional[str] = None

    address_line_1: str

    address_line_2: Optional[str] = None

    landmark: Optional[str] = None

    village: str

    city: str

    district: str

    state: str

    postal_code: str

    country: str

    latitude: Optional[Decimal] = None

    longitude: Optional[Decimal] = None

    farm_file_path: Optional[str] = None

    farm_file_content_type: Optional[str] = None

    created_at: datetime

    updated_at: datetime


# ============================================================
# FARM LIST RESPONSE
# ============================================================


class FarmListResponse(FarmSchemaBase):
    """
    Paginated list of the authenticated user's farms.
    """

    items: list[FarmResponse]

    total: int = Field(
        ...,
        ge=0,
    )

    offset: int = Field(
        ...,
        ge=0,
    )

    limit: int = Field(
        ...,
        ge=1,
        le=100,
    )


# ============================================================
# FARM FILE RESPONSE
# ============================================================


class FarmFileResponse(FarmSchemaBase):
    """
    Response returned after uploading/replacing a farm file.
    """

    farm: FarmResponse

    farm_file_url: str = Field(
        ...,
        min_length=1,
    )


# ============================================================
# FARM FILE URL RESPONSE
# ============================================================


class FarmFileUrlResponse(FarmSchemaBase):
    """
    Response containing a temporary signed URL for a farm file.
    """

    farm_file_url: str = Field(
        ...,
        min_length=1,
    )


# ============================================================
# MESSAGE RESPONSE
# ============================================================


class MessageResponse(FarmSchemaBase):
    """
    Generic successful-operation message.
    """

    message: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )