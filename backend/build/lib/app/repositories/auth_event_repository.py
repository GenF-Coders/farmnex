from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_event import AuthEvent
from app.core.enums import AuthEventType


class AuthEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================
    # CREATE
    # =========================================================

    async def create(
        self,
        *,
        event_type: AuthEventType,
        user_id: int | None = None,
        phone_number: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        failure_reason: str | None = None,
    ) -> AuthEvent:
        event = AuthEvent(
            event_type=event_type,
            user_id=user_id,
            phone_number=phone_number,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason,
        )

        self.session.add(event)
        await self.session.flush()

        return event

    # =========================================================
    # READ
    # =========================================================

    async def get_by_id(
        self,
        event_id: int,
    ) -> AuthEvent | None:
        result = await self.session.execute(
            select(AuthEvent).where(
                AuthEvent.id == event_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id,
    ) -> AuthEvent | None:
        result = await self.session.execute(
            select(AuthEvent).where(
                AuthEvent.public_id == public_id
            )
        )

        return result.scalar_one_or_none()

    async def get_user_events(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuthEvent]:
        result = await self.session.execute(
            select(AuthEvent)
            .where(
                AuthEvent.user_id == user_id
            )
            .order_by(
                AuthEvent.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_events_by_type(
        self,
        event_type: AuthEventType,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuthEvent]:
        result = await self.session.execute(
            select(AuthEvent)
            .where(
                AuthEvent.event_type == event_type
            )
            .order_by(
                AuthEvent.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_login_history(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuthEvent]:
        result = await self.session.execute(
            select(AuthEvent)
            .where(
                AuthEvent.user_id == user_id,
                AuthEvent.event_type.in_(
                    [
                        AuthEventType.LOGIN_SUCCESS,
                        AuthEventType.LOGIN_FAILED,
                    ]
                ),
            )
            .order_by(
                AuthEvent.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_failed_login_history(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AuthEvent]:
        result = await self.session.execute(
            select(AuthEvent)
            .where(
                AuthEvent.user_id == user_id,
                AuthEvent.event_type
                == AuthEventType.LOGIN_FAILED,
            )
            .order_by(
                AuthEvent.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_events_by_phone(
        self,
        phone_number: str,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuthEvent]:
        result = await self.session.execute(
            select(AuthEvent)
            .where(
                AuthEvent.phone_number == phone_number
            )
            .order_by(
                AuthEvent.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    # =========================================================
    # COUNT
    # =========================================================

    async def count_user_events(
        self,
        user_id: int,
    ) -> int:
        result = await self.session.execute(
            select(func.count(AuthEvent.id))
            .where(
                AuthEvent.user_id == user_id
            )
        )

        return result.scalar_one()

    async def count_events_by_type(
        self,
        event_type: AuthEventType,
    ) -> int:
        result = await self.session.execute(
            select(func.count(AuthEvent.id))
            .where(
                AuthEvent.event_type == event_type
            )
        )

        return result.scalar_one()

    # =========================================================
    # DATE RANGE
    # =========================================================

    async def get_events_between(
        self,
        start_time: datetime,
        end_time: datetime,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[AuthEvent]:
        result = await self.session.execute(
            select(AuthEvent)
            .where(
                AuthEvent.created_at >= start_time,
                AuthEvent.created_at < end_time,
            )
            .order_by(
                AuthEvent.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    # =========================================================
    # DELETE
    # =========================================================

    async def delete(
        self,
        event_id: int,
    ) -> bool:
        result = await self.session.execute(
            delete(AuthEvent)
            .where(
                AuthEvent.id == event_id
            )
        )

        await self.session.flush()

        return result.rowcount > 0