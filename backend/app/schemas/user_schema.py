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
# ROLE
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

    Only generic editable profile fields are exposed here.

    Authentication/system fields such as:
        - id
        - public_id
        - phone_number
        - role
        - account_status
        - PIN
        - verification timestamps
        - profile image path
        - login timestamps

    are deliberately excluded.
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
    """
    Public representation of a User.

    Sensitive/internal fields are intentionally excluded.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    public_id: UUID

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    phone_number: str

    phone_verified_at: datetime | None = None

    # --------------------------------------------------------
    # Role / account
    # --------------------------------------------------------

    role: RoleResponse

    account_status: str

    # --------------------------------------------------------
    # Generic profile
    # --------------------------------------------------------

    first_name: str | None = None

    middle_name: str | None = None

    surname: str | None = None

    alternate_phone_number: str | None = None

    alternate_phone_verified_at: datetime | None = None

    date_of_birth: date | None = None

    gender: str | None = None

    # --------------------------------------------------------
    # Profile image
    # --------------------------------------------------------

    profile_image_url: str | None = None

    # --------------------------------------------------------
    # Preferences / additional profile
    # --------------------------------------------------------

    preferred_language: str | None = None

    timezone: str | None = None

    occupation: str | None = None

    bio: str | None = None

    # --------------------------------------------------------
    # Timestamps
    # --------------------------------------------------------

    created_at: datetime

    updated_at: datetime

    last_login_at: datetime | None = None


# ============================================================
# PROFILE IMAGE UPLOAD RESPONSE
# ============================================================


class ProfileImageResponse(BaseModel):
    """
    Returned after uploading or replacing a profile image.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    user: UserResponse

    profile_image_url: str


# ============================================================
# PROFILE IMAGE URL RESPONSE
# ============================================================


class ProfileImageUrlResponse(BaseModel):
    """
    Returned when requesting a signed profile-image URL.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    profile_image_url: str


# ============================================================
# MESSAGE RESPONSE
# ============================================================


class MessageResponse(BaseModel):
    """
    Generic successful-operation response.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    message: str