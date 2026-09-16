from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_session import UserSession


class UserSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================
    # CREATE
    # =========================================================

    async def create(
        self,
        *,
        user_id: int,
        refresh_token_hash: str,
        expires_at: datetime,
        token_family: UUID | None = None,
        public_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=refresh_token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        if token_family is not None:
            session.token_family = token_family

        if public_id is not None:
            session.public_id = public_id

        self.session.add(session)

        await self.session.flush()

        return session

    # =========================================================
    # READ
    # =========================================================

    async def get_by_id(
        self,
        session_id: int,
    ) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.id == session_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.public_id == public_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_refresh_token_hash(
        self,
        refresh_token_hash: str,
    ) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession).where(
                UserSession.refresh_token_hash
                == refresh_token_hash
            )
        )

        return result.scalar_one_or_none()

    async def get_active_by_refresh_token_hash(
        self,
        refresh_token_hash: str,
        now: datetime,
    ) -> UserSession | None:
        result = await self.session.execute(
            select(UserSession)
            .where(
                UserSession.refresh_token_hash
                == refresh_token_hash,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
        )

        return result.scalar_one_or_none()

    async def get_active_sessions_for_user(
        self,
        user_id: int,
        now: datetime,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[UserSession]:
        result = await self.session.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .order_by(
                UserSession.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_sessions_for_user(
        self,
        user_id: int,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[UserSession]:
        result = await self.session.execute(
            select(UserSession)
            .where(
                UserSession.user_id == user_id
            )
            .order_by(
                UserSession.created_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_by_token_family(
        self,
        token_family: UUID,
    ) -> list[UserSession]:
        result = await self.session.execute(
            select(UserSession)
            .where(
                UserSession.token_family == token_family
            )
            .order_by(
                UserSession.created_at.asc()
            )
        )

        return list(result.scalars().all())

    # =========================================================
    # EXISTS
    # =========================================================

    async def exists_by_id(
        self,
        session_id: int,
    ) -> bool:
        result = await self.session.execute(
            select(UserSession.id)
            .where(
                UserSession.id == session_id
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_active_session_for_user(
        self,
        user_id: int,
        now: datetime,
    ) -> bool:
        result = await self.session.execute(
            select(UserSession.id)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    # =========================================================
    # UPDATE
    # =========================================================

    async def update(
        self,
        session_id: int,
        **values,
    ) -> UserSession | None:
        await self.session.execute(
            update(UserSession)
            .where(
                UserSession.id == session_id
            )
            .values(**values)
        )

        await self.session.flush()

        return await self.get_by_id(session_id)

    async def update_last_used(
        self,
        session_id: int,
        last_used_at: datetime,
    ) -> None:
        await self.session.execute(
            update(UserSession)
            .where(
                UserSession.id == session_id
            )
            .values(
                last_used_at=last_used_at
            )
        )

        await self.session.flush()

    async def rotate_refresh_token(
        self,
        session_id: int,
        *,
        refresh_token_hash: str,
        expires_at: datetime,
        last_used_at: datetime,
    ) -> UserSession | None:
        await self.session.execute(
            update(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.revoked_at.is_(None),
            )
            .values(
                refresh_token_hash=refresh_token_hash,
                expires_at=expires_at,
                last_used_at=last_used_at,
            )
        )

        await self.session.flush()

        return await self.get_by_id(session_id)

    # =========================================================
    # REVOKE
    # =========================================================

    async def revoke(
        self,
        session_id: int,
        revoked_at: datetime,
    ) -> bool:
        result = await self.session.execute(
            update(UserSession)
            .where(
                UserSession.id == session_id,
                UserSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at
            )
        )

        await self.session.flush()

        return result.rowcount > 0

    async def revoke_all_for_user(
        self,
        user_id: int,
        revoked_at: datetime,
    ) -> int:
        result = await self.session.execute(
            update(UserSession)
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at
            )
        )

        await self.session.flush()

        return result.rowcount

    async def revoke_token_family(
        self,
        token_family: UUID,
        revoked_at: datetime,
    ) -> int:
        result = await self.session.execute(
            update(UserSession)
            .where(
                UserSession.token_family == token_family,
                UserSession.revoked_at.is_(None),
            )
            .values(
                revoked_at=revoked_at
            )
        )

        await self.session.flush()

        return result.rowcount

    # =========================================================
    # COUNT
    # =========================================================

    async def count_for_user(
        self,
        user_id: int,
    ) -> int:
        result = await self.session.execute(
            select(func.count(UserSession.id))
            .where(
                UserSession.user_id == user_id
            )
        )

        return result.scalar_one()

    async def count_active_for_user(
        self,
        user_id: int,
        now: datetime,
    ) -> int:
        result = await self.session.execute(
            select(func.count(UserSession.id))
            .where(
                UserSession.user_id == user_id,
                UserSession.revoked_at.is_(None),
                UserSession.expires_at > now,
            )
        )

        return result.scalar_one()

    # =========================================================
    # DELETE / CLEANUP
    # =========================================================

    async def delete(
        self,
        session_id: int,
    ) -> bool:
        result = await self.session.execute(
            delete(UserSession)
            .where(
                UserSession.id == session_id
            )
        )

        await self.session.flush()

        return result.rowcount > 0

    async def delete_expired(
        self,
        now: datetime,
    ) -> int:
        result = await self.session.execute(
            delete(UserSession)
            .where(
                UserSession.expires_at <= now
            )
        )

        await self.session.flush()

        return result.rowcount