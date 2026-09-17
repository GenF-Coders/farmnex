from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import get_auth_service
from app.schemas.auth.auth import (
    AuthTokenResponse,
    AuthUserResponse,
    LoginRequestOTPRequest,
    LoginVerifyRequest,
    LogoutRequest,
    OTPAuthRequestResponse,
    RefreshTokenRequest,
    RegisterCompleteRequest,
    RegisterRequestOTPRequest,
    RegisterVerifyRequest,
)
from app.services.auth_service import AuthService
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


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ================================================================
# RESPONSE HELPERS
# ================================================================


def _user_response(user) -> AuthUserResponse:
    """
    Convert the internal User ORM object into the public
    authentication response.

    Internal fields such as id, role_id, pin_hash, timestamps,
    session identifiers, and token hashes are never exposed.
    """

    role_name = user.role.name if user.role is not None else None

    account_status = user.account_status
    if hasattr(account_status, "value"):
        account_status = account_status.value
    else:
        account_status = str(account_status)

    return AuthUserResponse(
        public_id=str(user.public_id),
        phone_number=user.phone_number,
        role=role_name,
        account_status=account_status,
        phone_verified=user.phone_verified_at is not None,
    )


def _token_response(
    user,
    access_token: str,
    refresh_token: str,
    expires_in: int,
) -> AuthTokenResponse:
    """Build the public authentication token response."""

    return AuthTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=_user_response(user),
    )


# ================================================================
# REGISTRATION
# ================================================================


@router.post(
    "/register/request-otp",
    response_model=OTPAuthRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request registration OTP",
)
async def register_request_otp(
    payload: RegisterRequestOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> OTPAuthRequestResponse:
    """
    Start registration by sending an OTP.

    Frontend sends only:
        {
            "phone_number": "9876543210"
        }

    The backend determines the OTP purpose as REGISTER.
    The frontend must not send provider OTP IDs, database IDs,
    role_id, session data, or other internal fields.
    """

    try:
        result = await auth_service.request_registration_otp(
            phone_number=payload.phone_number,
        )

        return OTPAuthRequestResponse(
            **result.model_dump()
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except OTPResendCooldownError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except OTPProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please try again later.",
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP service is temporarily unavailable.",
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to send OTP at this time.",
        ) from exc


@router.post(
    "/register/resend",
    response_model=OTPAuthRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend registration OTP",
)
async def register_resend_otp(
    payload: RegisterRequestOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> OTPAuthRequestResponse:
    """
    Resend the registration OTP.

    Frontend sends only:
        {
            "phone_number": "9876543210"
        }

    The backend determines the OTP purpose as REGISTER.
    """

    try:
        result = await auth_service.resend_registration_otp(
            phone_number=payload.phone_number,
        )

        return OTPAuthRequestResponse(
            **result.model_dump()
        )
        
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
        
    except OTPNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

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
            detail="Too many OTP requests. Please try again later.",
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP service is temporarily unavailable.",
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to resend OTP at this time.",
        ) from exc


@router.post(
    "/register/verify",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Verify registration OTP",
)
async def register_verify_otp(
    payload: RegisterVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Verify the registration OTP.

    Frontend sends only:
        {
            "phone_number": "9876543210",
            "otp": "123456"
        }

    This endpoint verifies the OTP only.
    It does not create the user.

    A successful verification returns the short-lived
    registration proof/token required by /register/complete.
    """

    try:
        result = await auth_service.verify_registration_otp(
            phone_number=payload.phone_number,
            otp=payload.otp,
        )

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

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
            detail="Too many verification attempts. Please try again later.",
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP service is temporarily unavailable.",
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to verify OTP at this time.",
        ) from exc


@router.post(
    "/register/complete",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete registration",
)
async def register_complete(
    payload: RegisterCompleteRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    """
    Complete registration after successful OTP verification.

    Frontend sends only:
        {
            "registration_token": "...",
            "role": "BUYER"
        }

    The backend obtains the verified phone number from the
    registration proof/token.

    Public registration roles must be restricted by the service
    layer to FARMER and BUYER. The frontend never sends role_id.

    On success the backend creates the user/session/audit records
    and returns FarmNex access and refresh tokens.
    """

    try:
        (
            user,
            access_token,
            refresh_token,
            expires_in,
        ) = await auth_service.complete_registration(
            registration_token=payload.registration_token,
            role_name=payload.role,
        )

        return _token_response(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


# ================================================================
# LOGIN
# ================================================================


@router.post(
    "/login/request-otp",
    response_model=OTPAuthRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Request login OTP",
)
async def login_request_otp(
    payload: LoginRequestOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> OTPAuthRequestResponse:
    """
    Start OTP login.

    Frontend sends only:
        {
            "phone_number": "9876543210"
        }

    The backend determines the OTP purpose as LOGIN.
    """

    try:
        result = await auth_service.request_login_otp(
            phone_number=payload.phone_number,
        )

        return OTPAuthRequestResponse(
            **result.model_dump()
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    except OTPResendCooldownError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    except OTPProviderRateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many OTP requests. Please try again later.",
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP service is temporarily unavailable.",
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to send OTP at this time.",
        ) from exc


@router.post(
    "/login/resend",
    response_model=OTPAuthRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Resend login OTP",
)
async def login_resend_otp(
    payload: LoginRequestOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> OTPAuthRequestResponse:
    """
    Resend login OTP.

    Frontend sends only:
        {
            "phone_number": "9876543210"
        }

    The backend determines the OTP purpose as LOGIN.
    """

    try:
        result = await auth_service.resend_login_otp(
            phone_number=payload.phone_number,
        )

        return OTPAuthRequestResponse(
            **result.model_dump()
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or account.",
        )

    except OTPNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

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
            detail="Too many OTP requests. Please try again later.",
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP service is temporarily unavailable.",
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to resend OTP at this time.",
        ) from exc


@router.post(
    "/login/verify",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify login OTP",
)
async def login_verify_otp(
    payload: LoginVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    """
    Verify login OTP and create a FarmNex session.

    Frontend sends only:
        {
            "phone_number": "9876543210",
            "otp": "123456"
        }

    The service layer handles:
        - OTP verification
        - user lookup
        - account-status validation
        - last-login update
        - session creation
        - refresh-token hashing
        - access/refresh JWT creation
        - authentication audit event
    """

    try:
        (
            user,
            access_token,
            refresh_token,
            expires_in,
        ) = await auth_service.login(
            phone_number=payload.phone_number,
            otp=payload.otp,
        )

        return _token_response(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid phone number or account.",
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
            detail="Too many verification attempts. Please try again later.",
        ) from exc

    except (
        OTPProviderTimeoutError,
        OTPProviderUnavailableError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTP service is temporarily unavailable.",
        ) from exc

    except OTPProviderError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to verify OTP at this time.",
        ) from exc


# ================================================================
# REFRESH TOKEN
# ================================================================


@router.post(
    "/refresh",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthTokenResponse:
    """
    Rotate the refresh token and issue a new access token.

    Frontend sends only:
        {
            "refresh_token": "..."
        }

    The raw refresh token is never stored in the database.
    """

    try:
        (
            user,
            access_token,
            new_refresh_token,
            expires_in,
        ) = await auth_service.refresh(
            refresh_token=payload.refresh_token,
        )

        return _token_response(
            user=user,
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=expires_in,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from exc


# ================================================================
# LOGOUT
# ================================================================


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
)
async def logout(
    payload: LogoutRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """
    Revoke the current FarmNex session.

    Frontend sends only:
        {
            "refresh_token": "..."
        }

    The service finds the corresponding session and revokes it.
    """

    try:
        await auth_service.logout(
            refresh_token=payload.refresh_token,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        ) from exc

    return None
