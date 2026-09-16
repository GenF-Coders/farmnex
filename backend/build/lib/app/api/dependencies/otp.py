from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.otp_repository import OTPRepository
from app.services.otp.providers.minimoth import MiniMothOTPProvider
from app.services.otp.service import OTPService


def get_otp_service(
    db: AsyncSession = Depends(get_db),
) -> OTPService:
    return OTPService(
        otp_repository=OTPRepository(db),
        provider=MiniMothOTPProvider(),
    )
