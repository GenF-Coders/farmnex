from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import OTPPurpose


def normalize_indian_phone(value: str) -> str:
    value = value.strip()
    digits = re.sub(r"[\s\-()]", "", value)

    if digits.startswith("+91"):
        digits = digits[3:]
    elif digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]

    if (
        len(digits) != 10
        or not digits.isdigit()
        or digits[0] not in "6789"
    ):
        raise ValueError(
            "Enter a valid Indian mobile number."
        )

    return f"+91{digits}"


class OTPRequestRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
        examples=["9876543210"],
    )

    purpose: OTPPurpose

    _normalize_phone = field_validator(
        "phone_number"
    )(normalize_indian_phone)


class OTPResendRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
        examples=["9876543210"],
    )

    purpose: OTPPurpose

    _normalize_phone = field_validator(
        "phone_number"
    )(normalize_indian_phone)


class OTPVerifyRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    phone_number: str = Field(
        min_length=10,
        max_length=20,
        examples=["9876543210"],
    )

    purpose: OTPPurpose

    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        examples=["123456"],
    )

    _normalize_phone = field_validator(
        "phone_number"
    )(normalize_indian_phone)