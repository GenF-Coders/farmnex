from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


# ============================================================
# ROLE RESPONSE
# ============================================================


class RoleResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    public_id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================
# PROFILE UPDATE REQUEST
# ============================================================


class UserProfileUpdateRequest(BaseModel):
    """
    Generic authenticated-user profile update.

    Authentication/system fields are deliberately excluded.
    Unknown frontend fields are ignored, while UserService
    performs the final business-field whitelist.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    first_name: str | None = Field(
        default=None,
        max_length=100,
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100,
    )

    surname: str | None = Field(
        default=None,
        max_length=100,
    )

    alternate_phone_number: str | None = Field(
        default=None,
        max_length=20,
    )

    date_of_birth: date | None = None

    gender: str | None = Field(
        default=None,
        max_length=30,
    )

    preferred_language: str | None = Field(
        default=None,
        max_length=20,
    )

    timezone: str | None = Field(
        default=None,
        max_length=50,
    )

    occupation: str | None = Field(
        default=None,
        max_length=150,
    )

    bio: str | None = Field(
        default=None,
        max_length=5000,
    )

    @field_validator(
        "first_name",
        "middle_name",
        "surname",
        "alternate_phone_number",
        "gender",
        "preferred_language",
        "timezone",
        "occupation",
        "bio",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


# ============================================================
# USER RESPONSE
# ============================================================


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    public_id: UUID

    phone_number: str
    phone_verified_at: datetime | None = None

    role: RoleResponse

    account_status: str

    first_name: str | None = None
    middle_name: str | None = None
    surname: str | None = None

    alternate_phone_number: str | None = None
    alternate_phone_verified_at: datetime | None = None

    date_of_birth: date | None = None
    gender: str | None = None

    profile_image_url: str | None = None

    preferred_language: str | None = None
    timezone: str | None = None
    occupation: str | None = None
    bio: str | None = None

    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None


# ============================================================
# PROFILE IMAGE RESPONSE
# ============================================================


class ProfileImageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    user: UserResponse
    profile_image_url: str


class ProfileImageUrlResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    profile_image_url: str


# ============================================================
# MESSAGE RESPONSE
# ============================================================


class MessageResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    message: str
