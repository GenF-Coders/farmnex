from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.otp import get_otp_service

from app.schemas.auth.otp import (
    OTPRequestRequest,
    OTPResendRequest,
    OTPVerifyRequest,
)
from app.services.otp.exceptions import (
    OTPAlreadyVerifiedError,
    OTPExpiredError,
    OTPInvalidError,
    OTPMaxAttemptsExceededError,
    OTPNotFoundError,
    OTPProviderError,
    OTPProviderRateLimitError,
    OTPProviderTimeoutError,
    OTPProviderUnavailableError,
    OTPResendCooldownError,
    OTPResendLimitExceededError,
)
from app.services.otp.schemas import (
    OTPRequestResult,
    OTPVerifyResult,
)
from app.services.otp.service import OTPService


router = APIRouter(
    prefix="/auth/otp",
    tags=["Authentication - OTP"],
)



@router.post(
    "/request",
    response_model=OTPRequestResult,
    status_code=status.HTTP_200_OK,
    summary="Request OTP",
)
async def request_otp(
    payload: OTPRequestRequest,
    otp_service: OTPService = Depends(
        get_otp_service
    ),
) -> OTPRequestResult:
    try:
        return await otp_service.request_otp(
            phone_number=payload.phone_number,
            purpose=payload.purpose,
        )

    except OTPResendCooldownError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except OTPProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many OTP requests. "
                "Please try again later."
            ),
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OTP service is temporarily "
                "unavailable."
            ),
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Unable to send OTP at this time."
            ),
        ) from exc


@router.post(
    "/resend",
    response_model=OTPRequestResult,
    status_code=status.HTTP_200_OK,
    summary="Resend OTP",
)
async def resend_otp(
    payload: OTPResendRequest,
    otp_service: OTPService = Depends(
        get_otp_service
    ),
) -> OTPRequestResult:
    try:
        return await otp_service.resend_otp(
            phone_number=payload.phone_number,
            purpose=payload.purpose,
        )

    except OTPResendCooldownError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except OTPResendLimitExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except OTPAlreadyVerifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except OTPProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many OTP requests. "
                "Please try again later."
            ),
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OTP service is temporarily "
                "unavailable."
            ),
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Unable to resend OTP at this time."
            ),
        ) from exc


@router.post(
    "/verify",
    response_model=OTPVerifyResult,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP",
)
async def verify_otp(
    payload: OTPVerifyRequest,
    otp_service: OTPService = Depends(
        get_otp_service
    ),
) -> OTPVerifyResult:
    try:
        return await otp_service.verify_otp(
            phone_number=payload.phone_number,
            purpose=payload.purpose,
            otp=payload.otp,
        )

    except OTPNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except OTPExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=str(exc),
        ) from exc

    except OTPAlreadyVerifiedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except OTPMaxAttemptsExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except OTPInvalidError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP.",
        ) from exc

    except OTPProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many verification attempts. "
                "Please try again later."
            ),
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "OTP service is temporarily "
                "unavailable."
            ),
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Unable to verify OTP at this time."
            ),
        ) from exc