from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ================================================================
# COMMON VALIDATION
# ================================================================


def _normalize_indian_phone(value: str) -> str:
    """
    Normalize an Indian mobile number to E.164 format.

    Accepted examples:
        9876543210
        +919876543210
        +91 9876543210
        +91-9876543210
        (9876543210)

    Stored/transmitted application value:
        +919876543210
    """

    if not isinstance(value, str):
        raise ValueError("Phone number must be a string.")

    phone = value.strip()

    # Remove presentation characters only.
    phone = re.sub(r"[\s\-()]", "", phone)

    if phone.startswith("+91"):
        digits = phone[3:]
    elif phone.startswith("91") and len(phone) == 12:
        digits = phone[2:]
    else:
        digits = phone

    if not re.fullmatch(r"[6-9]\d{9}", digits):
        raise ValueError("Enter a valid Indian mobile number.")

    return f"+91{digits}"


def _validate_otp(value: str) -> str:
    """Validate the six-digit OTP supplied by the frontend."""

    if not isinstance(value, str):
        raise ValueError("OTP must be a string.")

    otp = value.strip()

    if not re.fullmatch(r"\d{6}", otp):
        raise ValueError("OTP must be exactly 6 digits.")

    return otp


# ================================================================
# PUBLIC REGISTRATION ROLE
# ================================================================


RegistrationRole = Literal["FARMER", "CUSTOMER"]


# ================================================================
# REGISTRATION REQUESTS
# ================================================================


class RegisterRequestOTPRequest(BaseModel):
    """
    Request an OTP for public registration.

    Frontend may send only:
        {
            "phone_number": "9876543210"
        }
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=16,
        description="Indian mobile number.",
        examples=["9876543210"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        return _normalize_indian_phone(value)


class RegisterVerifyRequest(BaseModel):
    """
    Verify a registration OTP.

    Frontend may send only:
        {
            "phone_number": "9876543210",
            "otp": "123456"
        }

    This request does not contain role_id or any internal database field.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=16,
        examples=["9876543210"],
    )

    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        examples=["123456"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        return _normalize_indian_phone(value)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        return _validate_otp(value)


class RegisterCompleteRequest(BaseModel):
    """
    Complete registration after OTP verification.

    Frontend may send only:
        {
            "registration_token": "...",
            "role": "FARMER"
        }

    The phone number is intentionally not accepted here. The backend
    obtains the verified phone from the registration proof/token.
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    registration_token: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Short-lived proof returned after registration OTP verification.",
    )

    role: RegistrationRole = Field(
        ...,
        description="Public registration role.",
        examples=["FARMER"],
    )

    @field_validator("registration_token")
    @classmethod
    def validate_registration_token(cls, value: str) -> str:
        token = value.strip()

        if not token:
            raise ValueError("Registration token is required.")

        return token


# ================================================================
# LOGIN REQUESTS
# ================================================================


class LoginRequestOTPRequest(BaseModel):
    """
    Request an OTP for login.

    Frontend may send only:
        {
            "phone_number": "9876543210"
        }
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=16,
        examples=["9876543210"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        return _normalize_indian_phone(value)


class LoginVerifyRequest(BaseModel):
    """
    Verify a login OTP.

    Frontend may send only:
        {
            "phone_number": "9876543210",
            "otp": "123456"
        }
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=16,
        examples=["9876543210"],
    )

    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        examples=["123456"],
    )

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        return _normalize_indian_phone(value)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        return _validate_otp(value)


# ================================================================
# TOKEN REQUESTS
# ================================================================


class RefreshTokenRequest(BaseModel):
    """
    Refresh an authenticated FarmNex session.

    Frontend may send only:
        {
            "refresh_token": "..."
        }
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    refresh_token: str = Field(
        ...,
        min_length=1,
        max_length=4096,
    )

    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, value: str) -> str:
        token = value.strip()

        if not token:
            raise ValueError("Refresh token is required.")

        return token


class LogoutRequest(BaseModel):
    """
    Revoke the current FarmNex session.

    Frontend may send only:
        {
            "refresh_token": "..."
        }
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    refresh_token: str = Field(
        ...,
        min_length=1,
        max_length=4096,
    )

    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, value: str) -> str:
        token = value.strip()

        if not token:
            raise ValueError("Refresh token is required.")

        return token


# ================================================================
# OTP RESPONSE
# ================================================================


class OTPAuthRequestResponse(BaseModel):
    """
    Public response returned after an OTP is requested/resend.

    No provider API key, internal OTP database ID, phone hash,
    database primary key, or other internal information is exposed.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    otp_id: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Provider OTP request identifier.",
    )

    expires_in_seconds: int = Field(
        ...,
        ge=1,
        le=3600,
    )

    resend_available_in_seconds: int = Field(
        default=0,
        ge=0,
        le=3600,
    )


# ================================================================
# AUTHENTICATED USER RESPONSE
# ================================================================


class AuthUserResponse(BaseModel):
    """
    Public representation of the authenticated FarmNex user.

    Internal integer IDs, role_id, PIN hash, timestamps, and
    authentication/session internals are intentionally excluded.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    public_id: str = Field(
        ...,
        min_length=1,
        max_length=36,
    )

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=16,
    )

    role: str | None = Field(
        default=None,
        max_length=50,
    )

    account_status: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    phone_verified: bool


# ================================================================
# AUTH TOKEN RESPONSE
# ================================================================


class AuthTokenResponse(BaseModel):
    """
    Public token response.

    The backend returns the FarmNex access token and refresh token.
    """

    model_config = ConfigDict(
        extra="forbid",
    )

    access_token: str = Field(
        ...,
        min_length=1,
        max_length=8192,
    )

    refresh_token: str = Field(
        ...,
        min_length=1,
        max_length=8192,
    )

    expires_in: int = Field(
        ...,
        ge=1,
    )

    user: AuthUserResponse
