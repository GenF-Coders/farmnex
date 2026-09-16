from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class OTPProviderStatus(StrEnum):
    SENT = "SENT"
    FAILED = "FAILED"


class OTPSendResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool
    status: OTPProviderStatus
    provider_name: str
    provider_request_id: str | None = None
    message: str | None = None


class OTPProviderVerifyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    provider_name: str
    provider_identity_id: str | None = None
    message: str | None = None


class OTPRequestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    otp_id: str
    expires_in_seconds: int
    resend_available_in_seconds: int


class OTPVerifyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verified: bool
    otp_id: str
    provider_identity_id: str | None = None