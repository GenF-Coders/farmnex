from __future__ import annotations

from uuid import UUID

from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
    ):
        self.user_repository = user_repository
        self.role_repository = role_repository

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.user_repository.get_by_id(user_id)

    async def get_by_public_id(self, public_id: UUID) -> User | None:
        return await self.user_repository.get_by_public_id(public_id)

    async def get_by_phone(self, phone_number: str) -> User | None:
        return await self.user_repository.get_by_phone(phone_number)

    async def exists_by_phone(self, phone_number: str) -> bool:
        return await self.user_repository.exists_by_phone(phone_number)

    async def create(
        self,
        phone_number: str,
        role_id: int,
        pin_hash: str | None = None,
    ) -> User:
        existing_user = await self.user_repository.get_by_phone(phone_number)

        if existing_user is not None:
            raise ValueError("User with this phone number already exists.")

        role = await self.role_repository.get_by_id(role_id)

        if role is None:
            raise ValueError("Role not found.")

        user = User(
            phone_number=phone_number,
            role_id=role.id,
            pin_hash=pin_hash,
        )

        return await self.user_repository.create(user)

    async def update_role(
        self,
        user: User,
        role_id: int,
    ) -> User:
        role = await self.role_repository.get_by_id(role_id)

        if role is None:
            raise ValueError("Role not found.")

        user.role_id = role.id

        return await self.user_repository.update(user)

    async def update_pin(
        self,
        user: User,
        pin_hash: str,
    ) -> User:
        user.pin_hash = pin_hash

        return await self.user_repository.update(user)

    async def change_account_status(
        self,
        user: User,
        status,
    ) -> User:
        user.account_status = status

        return await self.user_repository.update(user)

    async def mark_phone_verified(
        self,
        user: User,
    ) -> User:
        from datetime import datetime, timezone

        user.phone_verified_at = datetime.now(timezone.utc)

        return await self.user_repository.update(user)

    async def update_last_login(
        self,
        user: User,
    ) -> User:
        from datetime import datetime, timezone

        user.last_login_at = datetime.now(timezone.utc)

        return await self.user_repository.update(user)

