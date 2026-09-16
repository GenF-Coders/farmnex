from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.auth_event_repository import AuthEventRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.repositories.user_session_repository import UserSessionRepository
from app.services.auth_service import AuthService
from app.services.otp.providers.minimoth import MiniMothOTPProvider
from app.services.otp.service import OTPService
from app.repositories.otp_repository import OTPRepository


def get_auth_service(
    db: AsyncSession = Depends(get_db),
) -> AuthService:
    return AuthService(
        user_repository=UserRepository(db),
        role_repository=RoleRepository(db),
        session_repository=UserSessionRepository(db),
        auth_event_repository=AuthEventRepository(db),
        otp_service=OTPService(
            otp_repository=OTPRepository(db),
            provider=MiniMothOTPProvider(),
        ),
    )
