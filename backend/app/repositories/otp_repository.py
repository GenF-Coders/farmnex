from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import OTPPurpose
from app.models.otp_verifications import OTPVerification


class OTPRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
        provider_name: str,
        provider_request_id: str,
        expires_at: datetime,
        max_attempts: int = 5,
        resend_count: int = 0,
        last_sent_at: datetime | None = None,
    ) -> OTPVerification:
        otp = OTPVerification(
            phone_number=phone_number,
            purpose=purpose,
            provider_name=provider_name,
            provider_request_id=provider_request_id,
            expires_at=expires_at,
            max_attempts=max_attempts,
            resend_count=resend_count,
        )

        if last_sent_at is not None:
            otp.last_sent_at = last_sent_at

        self.session.add(otp)
        await self.session.flush()

        return otp

    async def get_by_id(
        self,
        otp_id: int,
    ) -> OTPVerification | None:
        result = await self.session.execute(
            select(OTPVerification).where(
                OTPVerification.id == otp_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> OTPVerification | None:
        result = await self.session.execute(
            select(OTPVerification).where(
                OTPVerification.public_id == public_id
            )
        )

        return result.scalar_one_or_none()

    async def get_latest(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
    ) -> OTPVerification | None:
        result = await self.session.execute(
            select(OTPVerification)
            .where(
                OTPVerification.phone_number == phone_number,
                OTPVerification.purpose == purpose,
            )
            .order_by(
                OTPVerification.created_at.desc(),
                OTPVerification.id.desc(),
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def get_latest_valid(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
        now: datetime,
    ) -> OTPVerification | None:
        result = await self.session.execute(
            select(OTPVerification)
            .where(
                OTPVerification.phone_number == phone_number,
                OTPVerification.purpose == purpose,
                OTPVerification.expires_at > now,
                OTPVerification.verified_at.is_(None),
                OTPVerification.attempt_count
                < OTPVerification.max_attempts,
            )
            .order_by(
                OTPVerification.created_at.desc(),
                OTPVerification.id.desc(),
            )
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def get_all_for_phone(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[OTPVerification]:
        query = select(OTPVerification).where(
            OTPVerification.phone_number == phone_number
        )

        if purpose is not None:
            query = query.where(
                OTPVerification.purpose == purpose
            )

        query = (
            query
            .order_by(
                OTPVerification.created_at.desc(),
                OTPVerification.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def increment_attempt(
        self,
        otp_id: int,
    ) -> None:
        await self.session.execute(
            update(OTPVerification)
            .where(
                OTPVerification.id == otp_id,
                OTPVerification.verified_at.is_(None),
            )
            .values(
                attempt_count=(
                    OTPVerification.attempt_count + 1
                ),
            )
        )

        await self.session.flush()

    async def mark_verified(
        self,
        otp_id: int,
        *,
        verified_at: datetime,
    ) -> None:
        await self.session.execute(
            update(OTPVerification)
            .where(
                OTPVerification.id == otp_id,
                OTPVerification.verified_at.is_(None),
            )
            .values(
                verified_at=verified_at,
            )
        )

        await self.session.flush()

    async def invalidate_previous(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose,
        invalidated_at: datetime,
    ) -> None:
        await self.session.execute(
            update(OTPVerification)
            .where(
                OTPVerification.phone_number == phone_number,
                OTPVerification.purpose == purpose,
                OTPVerification.verified_at.is_(None),
            )
            .values(
                verified_at=invalidated_at,
            )
        )

        await self.session.flush()

    async def count_for_phone(
        self,
        *,
        phone_number: str,
        purpose: OTPPurpose | None = None,
    ) -> int:
        query = select(
            func.count(OTPVerification.id)
        ).where(
            OTPVerification.phone_number == phone_number
        )

        if purpose is not None:
            query = query.where(
                OTPVerification.purpose == purpose
            )

        result = await self.session.execute(query)

        return int(result.scalar_one())

    async def delete(
        self,
        otp_id: int,
    ) -> bool:
        result = await self.session.execute(
            delete(OTPVerification).where(
                OTPVerification.id == otp_id
            )
        )

        await self.session.flush()

        return result.rowcount > 0

    async def delete_expired(
        self,
        *,
        now: datetime,
    ) -> int:
        result = await self.session.execute(
            delete(OTPVerification).where(
                OTPVerification.expires_at <= now
            )
        )

        await self.session.flush()

        return result.rowcount