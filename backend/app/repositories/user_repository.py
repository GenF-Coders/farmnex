from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        public_id: UUID | None = None,
        phone_number: str,
        role_id: int,
        phone_verified_at: datetime | None = None,
        pin_hash: str | None = None,
        account_status=None,
    ) -> User:
        values = {
            "phone_number": phone_number,
            "role_id": role_id,
            "phone_verified_at": phone_verified_at,
            "pin_hash": pin_hash,
        }
        if public_id is not None:
            values["public_id"] = public_id
        if account_status is not None:
            values["account_status"] = account_status

        user = User(**values)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.role)).where(User.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone_number: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def get_by_phone_with_role(self, phone_number: str) -> User | None:
        result = await self.session.execute(
            select(User).options(selectinload(User.role)).where(
                User.phone_number == phone_number
            )
        )
        return result.scalar_one_or_none()

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> list[User]:
        result = await self.session.execute(
            select(User).options(selectinload(User.role))
            .order_by(User.id.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def exists_by_id(self, user_id: int) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.id == user_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_phone(self, phone_number: str) -> bool:
        result = await self.session.execute(
            select(User.id).where(User.phone_number == phone_number).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return int(result.scalar_one())

    async def update(self, user_id: int, **values) -> User | None:
        await self.session.execute(
            update(User).where(User.id == user_id).values(**values)
        )
        await self.session.flush()
        return await self.get_by_id(user_id)

    async def update_last_login(self, user_id: int) -> User | None:
        return await self.update(user_id, last_login_at=func.now())

    async def update_phone(
        self, user_id: int, phone_number: str, phone_verified_at=None
    ) -> User | None:
        return await self.update(
            user_id,
            phone_number=phone_number,
            phone_verified_at=phone_verified_at,
        )

    async def update_role(self, user_id: int, role_id: int) -> User | None:
        return await self.update(user_id, role_id=role_id)

    async def update_account_status(self, user_id: int, account_status) -> User | None:
        return await self.update(user_id, account_status=account_status)

    async def update_pin_hash(self, user_id: int, pin_hash: str | None) -> User | None:
        return await self.update(user_id, pin_hash=pin_hash)

    async def delete(self, user_id: int) -> bool:
        result = await self.session.execute(
            delete(User).where(User.id == user_id)
        )
        await self.session.flush()
        return result.rowcount > 0
