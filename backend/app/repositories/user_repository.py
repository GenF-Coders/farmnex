from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_phone(self, phone_number: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.phone_number == phone_number)
        )
        return result.scalar_one_or_none()

    async def exists_by_phone(self, phone_number: str) -> bool:
        result = await self.db.execute(
            select(User.id)
            .where(User.phone_number == phone_number)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.db.flush()
        await self.db.refresh(user)
        return user