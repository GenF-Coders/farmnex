from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from jwt import InvalidTokenError

from app.core.config import settings
from app.core.enums import AccountStatus, AuthEventType, OTPPurpose
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_value,
    verify_value,
)
from app.models.user import User
from app.repositories.auth_event_repository import AuthEventRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository
from app.services.otp.exceptions import (
    OTPInvalidError,
    OTPNotFoundError,
)
from app.services.otp.schemas import OTPRequestResult
from app.services.otp.service import OTPService


class AuthService:
    """Application service for registration, OTP login and sessions."""


    def __init__(
        self,
        *,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        session_repository: UserSessionRepository,
        auth_event_repository: AuthEventRepository,
        otp_service: OTPService,
    ) -> None:
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.session_repository = session_repository
        self.auth_event_repository = auth_event_repository
        self.otp_service = otp_service

    def _validate_public_registration_role(self, role_name: str) -> str:
        """Normalize and validate a publicly selectable registration role."""

        role_name = role_name.strip().upper()

        if role_name not in settings.public_registration_roles:
            allowed_roles = ", ".join(settings.public_registration_roles)
            raise ValueError(
                f"Invalid registration role. Allowed roles: {allowed_roles}."
            )

        return role_name

    async def request_registration_otp(
        self,
        *,
        phone_number: str,
    ) -> OTPRequestResult:
        if not settings.enable_registration:
            raise ValueError("Registration is currently disabled.")

        existing = await self.user_repository.get_by_phone(phone_number)
        if existing is not None:
            raise ValueError(
                "An account with this phone number already exists."
            )

        return await self.otp_service.request_otp(
            phone_number=phone_number,
            purpose=OTPPurpose.REGISTER,
        )
        
    
    async def register(
        self,
        *,
        phone_number: str,
        role_name: str,
        otp: str,
    ) -> tuple[User, str, str, int]:
        """Legacy one-step registration contract.

        Kept for compatibility with older callers. New controller flow should
        use verify_registration_otp() followed by complete_registration().
        """
        if not settings.enable_registration:
            raise ValueError("Registration is currently disabled.")

        role_name = self._validate_public_registration_role(role_name)

        role = await self.role_repository.get_by_name(role_name)
        if role is None:
            raise ValueError(f"Role '{role_name}' is not configured.")

        existing = await self.user_repository.get_by_phone(phone_number)
        if existing is not None:
            raise ValueError("An account with this phone number already exists.")

        await self.otp_service.verify_otp(
            phone_number=phone_number,
            purpose=OTPPurpose.REGISTER,
            otp=otp,
        )

        return await self._create_registered_user(
            phone_number=phone_number,
            role_id=role.id,
        )

    async def verify_registration_otp(
        self,
        *,
        phone_number: str,
        otp: str,
    ) -> dict[str, str | int]:
        """Verify OTP and return a short-lived registration proof.

        The proof is a signed FarmNex JWT. It contains only the verified phone,
        a registration purpose marker, issued time and expiry. No user is
        created here and no session is created here.
        """
        if not settings.enable_registration:
            raise ValueError("Registration is currently disabled.")

        existing = await self.user_repository.get_by_phone(phone_number)
        if existing is not None:
            raise ValueError("An account with this phone number already exists.")

        await self.otp_service.verify_otp(
            phone_number=phone_number,
            purpose=OTPPurpose.REGISTER,
            otp=otp,
        )

        token = self._create_registration_token(phone_number)

        return {
            "registration_token": token,
            "expires_in": settings.registration_token_expire_minutes * 60,
        }

    async def complete_registration(
        self,
        *,
        registration_token: str,
        role_name: str,
    ) -> tuple[User, str, str, int]:
        """Create the account from a previously verified registration proof."""
        if not settings.enable_registration:
            raise ValueError("Registration is currently disabled.")

        phone_number = self._decode_registration_token(registration_token)

        role_name = self._validate_public_registration_role(role_name)

        role = await self.role_repository.get_by_name(role_name)
        if role is None:
            raise ValueError(f"Role '{role_name}' is not configured.")

        # The OTP verification itself is persisted by OTPService. We must
        # re-check the user immediately before creation to prevent normal
        # duplicate-registration races from being silently accepted.
        existing = await self.user_repository.get_by_phone(phone_number)
        if existing is not None:
            raise ValueError("An account with this phone number already exists.")

        return await self._create_registered_user(
            phone_number=phone_number,
            role_id=role.id,
        )

    async def request_login_otp(
        self,
        *,
        phone_number: str,
    ) -> OTPRequestResult:
        if not settings.enable_otp_login:
            raise ValueError("OTP login is currently disabled.")

        user = await self.user_repository.get_by_phone(phone_number)
        if user is None:
            raise ValueError("Invalid phone number or account.")

        if user.account_status != AccountStatus.ACTIVE:
            raise ValueError("This account is not active.")

        return await self.otp_service.request_otp(
            phone_number=phone_number,
            purpose=OTPPurpose.LOGIN,
        )

    async def login(
        self,
        *,
        phone_number: str,
        otp: str,
    ) -> tuple[User, str, str, int]:
        if not settings.enable_otp_login:
            raise ValueError("OTP login is currently disabled.")

        user = await self.user_repository.get_by_phone_with_role(phone_number)
        if user is None:
            raise ValueError("Invalid phone number or account.")

        if user.account_status != AccountStatus.ACTIVE:
            raise ValueError("This account is not active.")

        await self.otp_service.verify_otp(
            phone_number=phone_number,
            purpose=OTPPurpose.LOGIN,
            otp=otp,
        )

        updated_user = await self.user_repository.update_last_login(user.id)
        if updated_user is None:
            raise RuntimeError("User could not be updated after login.")

        user = await self.user_repository.get_by_phone_with_role(phone_number)
        if user is None:
            raise RuntimeError("User could not be loaded after login.")

        access_token, refresh_token, expires_in = await self._create_session(
            user=user,
        )

        await self.auth_event_repository.create(
            event_type=AuthEventType.OTP_VERIFIED,
            user_id=user.id,
            phone_number=user.phone_number,
        )
        await self.auth_event_repository.create(
            event_type=AuthEventType.LOGIN_SUCCESS,
            user_id=user.id,
            phone_number=user.phone_number,
        )

        return user, access_token, refresh_token, expires_in

    async def refresh(
        self,
        *,
        refresh_token: str,
    ) -> tuple[User, str, str, int]:
        if not refresh_token:
            raise ValueError("Invalid refresh token.")

        try:
            payload = decode_token(refresh_token)
        except (InvalidTokenError, ValueError, TypeError) as exc:
            raise ValueError("Invalid refresh token.") from exc
        except Exception as exc:
            raise ValueError("Invalid refresh token.") from exc

        if payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token.")

        session_id_raw = payload.get("session_id")
        user_id_raw = payload.get("sub")
        token_family_raw = payload.get("token_family")

        try:
            session_public_id = UUID(str(session_id_raw))
            user_public_id = UUID(str(user_id_raw))
            token_family = UUID(str(token_family_raw))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError("Invalid refresh token.") from exc

        session = await self.session_repository.get_by_public_id(
            session_public_id
        )
        if session is None:
            raise ValueError("Invalid refresh token.")

        now = datetime.now(timezone.utc)

        if session.revoked_at is not None:
            raise ValueError("Refresh token has been revoked.")

        if session.expires_at <= now:
            raise ValueError("Refresh token has expired.")

        if session.token_family != token_family:
            raise ValueError("Invalid refresh token.")

        # Argon2 verification is intentionally performed against the raw
        # presented refresh token; the raw token is never stored.
        if not verify_value(session.refresh_token_hash, refresh_token):
            raise ValueError("Invalid refresh token.")

        user = await self.user_repository.get_by_public_id(user_public_id)
        if user is None or user.id != session.user_id:
            raise ValueError("Invalid refresh token.")

        if user.account_status != AccountStatus.ACTIVE:
            raise ValueError("This account is not active.")

        new_refresh_token = create_refresh_token(
            user_id=user.public_id,
            session_id=session.public_id,
            token_family=session.token_family,
        )
        new_hash = hash_value(new_refresh_token)
        new_expires_at = now + timedelta(
            days=settings.refresh_token_expire_days
        )

        rotated = await self.session_repository.rotate_refresh_token(
            session.id,
            refresh_token_hash=new_hash,
            expires_at=new_expires_at,
            last_used_at=now,
        )
        if rotated is False:
            raise ValueError("Refresh token is no longer valid.")

        access_token = create_access_token(
            user_id=user.public_id,
            role=user.role.name if user.role else "BUYER",
        )

        return (
            user,
            access_token,
            new_refresh_token,
            settings.access_token_expire_minutes * 60,
        )

    async def logout(self, *, refresh_token: str) -> None:
        """Revoke the session represented by a valid refresh token.

        Logout is intentionally idempotent: malformed/already-revoked tokens
        do not disclose session information.
        """
        if not refresh_token:
            return

        try:
            payload = decode_token(refresh_token)
        except Exception:
            return

        if payload.get("type") != "refresh":
            return

        try:
            session_public_id = UUID(str(payload.get("session_id")))
        except (ValueError, TypeError, AttributeError):
            return

        session = await self.session_repository.get_by_public_id(
            session_public_id
        )
        if session is None or session.revoked_at is not None:
            return

        if verify_value(session.refresh_token_hash, refresh_token):
            await self.session_repository.revoke(
                session.id,
                datetime.now(timezone.utc),
            )

            user = await self.user_repository.get_by_id(session.user_id)
            if user is not None:
                await self.auth_event_repository.create(
                    event_type=AuthEventType.LOGOUT,
                    user_id=user.id,
                    phone_number=user.phone_number,
                )

    async def resend_registration_otp(
        self,
        *,
        phone_number: str,
    ) -> OTPRequestResult:
        if not settings.enable_registration:
            raise ValueError("Registration is currently disabled.")

        existing = await self.user_repository.get_by_phone(phone_number)
        if existing is not None:
            raise ValueError("An account with this phone number already exists.")

        return await self.otp_service.resend_otp(
            phone_number=phone_number,
            purpose=OTPPurpose.REGISTER,
        )

    async def resend_login_otp(
        self,
        *,
        phone_number: str,
    ) -> OTPRequestResult:
        if not settings.enable_otp_login:
            raise ValueError("OTP login is currently disabled.")

        user = await self.user_repository.get_by_phone(phone_number)
        if user is None or user.account_status != AccountStatus.ACTIVE:
            raise ValueError("Invalid phone number or account.")

        return await self.otp_service.resend_otp(
            phone_number=phone_number,
            purpose=OTPPurpose.LOGIN,
        )

    async def _create_registered_user(
        self,
        *,
        phone_number: str,
        role_id: int,
    ) -> tuple[User, str, str, int]:
        now = datetime.now(timezone.utc)

        user = await self.user_repository.create(
            public_id=uuid4(),
            phone_number=phone_number,
            role_id=role_id,
            phone_verified_at=now,
            account_status=AccountStatus.ACTIVE,
        )

        user = await self.user_repository.get_by_phone_with_role(phone_number)
        if user is None:
            raise RuntimeError("User could not be loaded after registration.")

        access_token, refresh_token, expires_in = await self._create_session(
            user=user,
        )

        await self.auth_event_repository.create(
            event_type=AuthEventType.OTP_VERIFIED,
            user_id=user.id,
            phone_number=user.phone_number,
        )
        await self.auth_event_repository.create(
            event_type=AuthEventType.LOGIN_SUCCESS,
            user_id=user.id,
            phone_number=user.phone_number,
        )

        return user, access_token, refresh_token, expires_in

    def _create_registration_token(self, phone_number: str) -> str:
        # Reuse the FarmNex JWT infrastructure, but mark this token with a
        # dedicated type so it can never be accepted as an access/refresh token.
        from app.core.security import create_registration_token

        return create_registration_token(phone_number=phone_number)

    def _decode_registration_token(self, token: str) -> str:
        if not token:
            raise ValueError("Invalid registration token.")

        try:
            payload = decode_token(token)
        except Exception as exc:
            raise ValueError("Invalid or expired registration token.") from exc

        if payload.get("type") != "registration":
            raise ValueError("Invalid registration token.")

        phone_number = payload.get("phone_number")
        if not isinstance(phone_number, str) or not phone_number:
            raise ValueError("Invalid registration token.")

        return phone_number

    async def _create_session(
        self,
        *,
        user: User,
    ) -> tuple[str, str, int]:
        now = datetime.now(timezone.utc)

        active_count = await self.session_repository.count_active_for_user(
            user.id,
            now,
        )

        if active_count >= settings.max_sessions_per_user:
            sessions = await self.session_repository.get_active_sessions_for_user(
                user.id,
                now,
                offset=0,
                limit=100,
            )

            oldest = sessions[-1] if sessions else None
            if oldest is not None:
                await self.session_repository.revoke(
                    oldest.id,
                    now,
                )

        session_public_id = uuid4()
        token_family = uuid4()

        refresh_token = create_refresh_token(
            user_id=user.public_id,
            session_id=session_public_id,
            token_family=token_family,
        )

        refresh_hash = hash_value(refresh_token)
        refresh_expires_at = now + timedelta(
            days=settings.refresh_token_expire_days
        )

        await self.session_repository.create(
            user_id=user.id,
            public_id=session_public_id,
            token_family=token_family,
            refresh_token_hash=refresh_hash,
            expires_at=refresh_expires_at,
        )

        access_token = create_access_token(
            user_id=user.public_id,
            role=user.role.name if user.role else "BUYER",
        )

        return (
            access_token,
            refresh_token,
            settings.access_token_expire_minutes * 60,
        )
