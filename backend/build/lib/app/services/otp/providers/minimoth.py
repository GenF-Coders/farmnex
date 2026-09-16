from __future__ import annotations

import re
from typing import Any

import httpx

from app.core.config import settings
from app.services.otp.exceptions import (
    OTPInvalidError,
    OTPNotFoundError,
    OTPProviderError,
    OTPProviderRateLimitError,
    OTPProviderTimeoutError,
    OTPProviderUnavailableError,
)
from app.services.otp.providers.base import OTPProvider
from app.services.otp.schemas import (
    OTPProviderStatus,
    OTPProviderVerifyResult,
    OTPSendResult,
)


class MiniMothOTPProvider(OTPProvider):
    @property
    def name(self) -> str:
        return "minimoth"

    # ============================================================
    # SEND OTP
    # ============================================================

    async def send_otp(
        self,
        *,
        phone_number: str,
    ) -> OTPSendResult:
        phone_number = self._normalize_phone(phone_number)

        response = await self._request(
            method="POST",
            path="/v1/otp/send",
            json={
                "phone": phone_number,
            },
        )

        data = self._parse_json(response)

        otp_id = data.get("otp_id")

        if not otp_id:
            raise OTPProviderError(
                "MiniMoth did not return an OTP ID."
            )

        return OTPSendResult(
            success=True,
            status=OTPProviderStatus.SENT,
            provider_name=self.name,
            provider_request_id=str(otp_id),
            message=data.get("message"),
        )

    # ============================================================
    # VERIFY OTP
    # ============================================================

    async def verify_otp(
        self,
        *,
        phone_number: str,
        otp: str,
    ) -> OTPProviderVerifyResult:
        phone_number = self._normalize_phone(phone_number)

        if not re.fullmatch(r"\d{6}", otp):
            raise OTPInvalidError(
                "OTP must contain exactly 6 digits."
            )

        response = await self._request(
            method="POST",
            path="/v1/otp/verify",
            json={
                "phone": phone_number,
                "code": otp,
            },
        )

        data = self._parse_json(response)

        return OTPProviderVerifyResult(
            verified=True,
            provider_name=self.name,
            provider_identity_id=data.get("identity_id"),
            message=data.get("message"),
        )

    # ============================================================
    # HTTP REQUEST
    # ============================================================

    async def _request(
        self,
        *,
        method: str,
        path: str,
        json: dict[str, Any],
    ) -> httpx.Response:
        if not settings.minimoth_api_key:
            raise OTPProviderError(
                "MiniMoth API key is not configured."
            )

        base_url = settings.minimoth_api_base_url.rstrip("/")
        url = f"{base_url}{path}"

        headers = {
            "X-Api-Key": settings.minimoth_api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(
                    settings.minimoth_timeout_seconds
                ),
            ) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json,
                )

                # Temporary diagnostic logging.
                # Remove or replace with proper application logging
                # before production.
                print(
                    "MINIMOTH STATUS:",
                    response.status_code,
                )
                print(
                    "MINIMOTH RESPONSE:",
                    response.text,
                )

        except httpx.TimeoutException as exc:
            raise OTPProviderTimeoutError(
                "MiniMoth request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise OTPProviderUnavailableError(
                "MiniMoth is currently unavailable."
            ) from exc

        self._raise_for_provider_error(response)

        return response

    # ============================================================
    # PROVIDER ERROR HANDLING
    # ============================================================

    @staticmethod
    def _raise_for_provider_error(
        response: httpx.Response,
    ) -> None:
        if response.is_success:
            return

        try:
            data = response.json()
        except ValueError:
            data = {}

        if not isinstance(data, dict):
            data = {}

        message = (
            data.get("error")
            or data.get("message")
            or (
                f"MiniMoth returned HTTP "
                f"{response.status_code}."
            )
        )

        code = data.get("code")

        # HTTP 429
        if response.status_code == 429:
            raise OTPProviderRateLimitError(message)

        # OTP verification errors
        if code == "INVALID_OTP":
            raise OTPInvalidError(message)

        if code == "OTP_NOT_FOUND":
            raise OTPNotFoundError(message)

        if code == "VERIFY_RATE_LIMITED":
            raise OTPProviderRateLimitError(message)

        # Authentication/provider configuration errors,
        # provider failures, etc.
        raise OTPProviderError(message)

    # ============================================================
    # JSON PARSING
    # ============================================================

    @staticmethod
    def _parse_json(
        response: httpx.Response,
    ) -> dict[str, Any]:
        try:
            data = response.json()
        except ValueError as exc:
            raise OTPProviderError(
                "MiniMoth returned an invalid response."
            ) from exc

        if not isinstance(data, dict):
            raise OTPProviderError(
                "MiniMoth returned an invalid response."
            )

        return data

    # ============================================================
    # PHONE NORMALIZATION
    # ============================================================

    @staticmethod
    def _normalize_phone(phone_number: str) -> str:
        phone_number = phone_number.strip()

        if not phone_number:
            raise OTPInvalidError(
                "Phone number is required."
            )

        # Remove spaces, hyphens, parentheses, etc.
        normalized = re.sub(
            r"[()\s-]",
            "",
            phone_number,
        )

        # Allow + followed by digits.
        if normalized.startswith("+"):
            digits = normalized[1:]
        else:
            digits = normalized

        if not digits.isdigit():
            raise OTPInvalidError(
                "Invalid phone number."
            )

        # India-specific normalization:
        # 9112391038 -> +919112391038
        if len(digits) == 10:
            if not digits.startswith(("6", "7", "8", "9")):
                raise OTPInvalidError(
                    "Invalid Indian mobile number."
                )

            digits = f"91{digits}"

        # Already international Indian number.
        elif len(digits) == 12 and digits.startswith("91"):
            pass

        else:
            raise OTPInvalidError(
                "Invalid phone number format."
            )

        return f"+{digits}"