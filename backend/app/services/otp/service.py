from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.enums import OTPPurpose
from app.repositories.otp_repository import OTPRepository
from app.services.otp.exceptions import (
    OTPAlreadyVerifiedError,
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsExceededError,
    OTPNotFoundError,
    OTPProviderError,
    OTPResendCooldownError,
    OTPResendLimitExceededError,
)
from app.services.otp.providers.base import OTPProvider
from app.services.otp.schemas import (
    OTPRequestResult,
    OTPVerifyResult,
)


class OTPService:
    def __init__(
        self,
        *,
        otp_repository: OTPRepository,
        provider: OTPProvider,
    ) -> None:
        self.otp_repository = otp_repository
        self.provider = provider

    async def request_otp(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
    ) -> OTPRequestResult:
        if not settings.otp_enabled:
            raise OTPProviderError("OTP service is currently disabled.")

        now = self._now()

        await self._check_resend_cooldown(
            phone_number=phone_number,
            purpose=purpose,
            now=now,
        )

        provider_result = await self.provider.send_otp(
            phone_number=phone_number,
        )

        if not provider_result.success:
            raise OTPProviderError(
                provider_result.message
                or "OTP provider failed to send OTP."
            )

        if not provider_result.provider_request_id:
            raise OTPProviderError(
                "OTP provider did not return a request ID."
            )

        expires_at = (
            now
            + timedelta(
                minutes=settings.otp_expire_minutes
            )
        )

        await self.otp_repository.invalidate_previous(
            phone_number=phone_number,
            purpose=purpose,
            invalidated_at=now,
        )

        otp_record = await self.otp_repository.create(
            phone_number=phone_number,
            purpose=purpose,
            provider_name=provider_result.provider_name,
            provider_request_id=(
                provider_result.provider_request_id
            ),
            expires_at=expires_at,
            max_attempts=settings.otp_max_attempts,
            resend_count=0,
            last_sent_at=now,
        )

        return self._build_request_result(
            otp_id=otp_record.public_id,
            expires_at=expires_at,
            now=now,
        )

    async def verify_otp(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
        otp: str,
    ) -> OTPVerifyResult:
        now = self._now()

        otp_record = (
            await self.otp_repository.get_latest_valid(
                phone_number=phone_number,
                purpose=purpose,
                now=now,
            )
        )

        if otp_record is None:
            latest = (
                await self.otp_repository.get_latest(
                    phone_number=phone_number,
                    purpose=purpose,
                )
            )

            if latest is None:
                raise OTPNotFoundError(
                    "No OTP request was found."
                )

            if latest.verified_at is not None:
                raise OTPAlreadyVerifiedError(
                    "This OTP has already been used."
                )

            if latest.expires_at <= now:
                raise OTPExpiredError(
                    "OTP has expired."
                )

            if (
                latest.attempt_count
                >= latest.max_attempts
            ):
                raise OTPMaxAttemptsExceededError(
                    "Maximum OTP verification attempts exceeded."
                )

            raise OTPNotFoundError(
                "No valid OTP was found."
            )

        await self.otp_repository.increment_attempt(
            otp_record.id
        )

        try:
            provider_result = (
                await self.provider.verify_otp(
                    phone_number=phone_number,
                    otp=otp,
                )
            )

        except OTPInvalidError:
            # Preserve failed-attempt accounting even though the
            # request will otherwise be rolled back by get_db().
            await self.otp_repository.session.commit()
            raise

        await self.otp_repository.mark_verified(
            otp_record.id,
            verified_at=now,
        )

        return OTPVerifyResult(
            verified=provider_result.verified,
            otp_id=str(otp_record.public_id),
            provider_identity_id=(
                provider_result.provider_identity_id
            ),
        )

    async def resend_otp(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
    ) -> OTPRequestResult:
        if not settings.otp_enabled:
            raise OTPProviderError("OTP service is currently disabled.")

        now = self._now()

        current = await self.otp_repository.get_latest(
            phone_number=phone_number,
            purpose=purpose,
        )

        if current is None:
            return await self.request_otp(
                phone_number=phone_number,
                purpose=purpose,
            )

        if current.verified_at is not None:
            raise OTPAlreadyVerifiedError(
                "The current OTP has already been verified."
            )

        if (
            current.resend_count
            >= settings.otp_max_resends
        ):
            raise OTPResendLimitExceededError(
                "Maximum OTP resend limit exceeded."
            )

        await self._check_resend_cooldown(
            phone_number=phone_number,
            purpose=purpose,
            now=now,
        )

        provider_result = await self.provider.send_otp(
            phone_number=phone_number,
        )

        if not provider_result.success:
            raise OTPProviderError(
                provider_result.message
                or "OTP provider failed to send OTP."
            )

        if not provider_result.provider_request_id:
            raise OTPProviderError(
                "OTP provider did not return a request ID."
            )

        expires_at = (
            now
            + timedelta(
                minutes=settings.otp_expire_minutes
            )
        )

        await self.otp_repository.invalidate_previous(
            phone_number=phone_number,
            purpose=purpose,
            invalidated_at=now,
        )

        otp_record = await self.otp_repository.create(
            phone_number=phone_number,
            purpose=purpose,
            provider_name=provider_result.provider_name,
            provider_request_id=(
                provider_result.provider_request_id
            ),
            expires_at=expires_at,
            max_attempts=settings.otp_max_attempts,
            resend_count=current.resend_count + 1,
            last_sent_at=now,
        )

        return self._build_request_result(
            otp_id=otp_record.public_id,
            expires_at=expires_at,
            now=now,
        )

    async def _check_resend_cooldown(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
        now: datetime,
    ) -> None:
        latest = await self.otp_repository.get_latest(
            phone_number=phone_number,
            purpose=purpose,
        )

        if latest is None:
            return

        if latest.verified_at is not None:
            return

        elapsed_seconds = (
            now - latest.last_sent_at
        ).total_seconds()

        cooldown_seconds = (
            settings.otp_resend_cooldown_seconds
        )

        if elapsed_seconds < cooldown_seconds:
            remaining_seconds = max(
                1,
                int(
                    cooldown_seconds
                    - elapsed_seconds
                ),
            )

            raise OTPResendCooldownError(
                f"Please wait {remaining_seconds} seconds "
                "before requesting another OTP."
            )

    @staticmethod
    def _build_request_result(
        *,
        otp_id,
        expires_at: datetime,
        now: datetime,
    ) -> OTPRequestResult:
        return OTPRequestResult(
            otp_id=str(otp_id),
            expires_in_seconds=max(
                0,
                int(
                    (
                        expires_at - now
                    ).total_seconds()
                ),
            ),
            resend_available_in_seconds=(
                settings.otp_resend_cooldown_seconds
            ),
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)