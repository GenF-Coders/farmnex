from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    surname: str = Field(min_length=1, max_length=100)

    alternate_phone_number: str | None = Field(
        default=None,
        min_length=10,
        max_length=20,
    )

    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=30)

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
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class ProfileUpdateRequest(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100,
    )

    surname: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    alternate_phone_number: str | None = Field(
        default=None,
        min_length=10,
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
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    user_id: int

    first_name: str
    middle_name: str | None
    surname: str

    alternate_phone_number: str | None
    alternate_phone_verified_at: datetime | None

    date_of_birth: date | None
    gender: str | None

    profile_image_url: str | None

    preferred_language: str | None
    timezone: str | None
    occupation: str | None
    bio: str | None

    created_at: datetime
    updated_at: datetime