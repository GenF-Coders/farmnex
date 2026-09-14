from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.enums import AccountStatus
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
    ) -> None:
        self.user_repository = user_repository
        self.role_repository = role_repository

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.user_repository.get_by_id(user_id)

    async def get_by_public_id(self, public_id: UUID) -> User | None:
        return await self.user_repository.get_by_public_id(public_id)

    async def get_by_phone(self, phone_number: str) -> User | None:
        return await self.user_repository.get_by_phone(phone_number)

    async def get_by_phone_with_role(self, phone_number: str) -> User | None:
        return await self.user_repository.get_by_phone_with_role(phone_number)

    async def exists_by_phone(self, phone_number: str) -> bool:
        return await self.user_repository.exists_by_phone(phone_number)

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        return await self.user_repository.get_all(
            offset=offset,
            limit=limit,
        )

    async def create(
        self,
        *,
        phone_number: str,
        role_id: int,
        pin_hash: str | None = None,
        phone_verified_at: datetime | None = None,
        account_status: AccountStatus = AccountStatus.ACTIVE,
    ) -> User:
        existing_user = await self.user_repository.get_by_phone(
            phone_number
        )

        if existing_user is not None:
            raise ValueError(
                "User with this phone number already exists."
            )

        role = await self.role_repository.get_by_id(role_id)

        if role is None:
            raise ValueError("Role not found.")

        return await self.user_repository.create(
            public_id=uuid4(),
            phone_number=phone_number,
            role_id=role.id,
            phone_verified_at=phone_verified_at,
            pin_hash=pin_hash,
            account_status=account_status,
        )

    async def create_with_role_name(
        self,
        *,
        phone_number: str,
        role_name: str,
        phone_verified_at: datetime | None = None,
    ) -> User:
        role = await self.role_repository.get_by_name(role_name)

        if role is None:
            raise ValueError(
                f"Role '{role_name}' is not available."
            )

        existing_user = await self.user_repository.get_by_phone(
            phone_number
        )

        if existing_user is not None:
            raise ValueError(
                "User with this phone number already exists."
            )

        return await self.user_repository.create(
            public_id=uuid4(),
            phone_number=phone_number,
            role_id=role.id,
            phone_verified_at=phone_verified_at,
            account_status=AccountStatus.ACTIVE,
        )

    async def update_role(
        self,
        user: User,
        role_id: int,
    ) -> User:
        role = await self.role_repository.get_by_id(role_id)

        if role is None:
            raise ValueError("Role not found.")

        return await self.user_repository.update_role(
            user.id,
            role.id,
        )

    async def update_pin(
        self,
        user: User,
        pin_hash: str,
    ) -> User:
        return await self.user_repository.update_pin_hash(
            user.id,
            pin_hash,
        )

    async def change_account_status(
        self,
        user: User,
        status: AccountStatus,
    ) -> User:
        return await self.user_repository.update_account_status(
            user.id,
            status,
        )

    async def mark_phone_verified(
        self,
        user: User,
    ) -> User:
        verified_at = datetime.now(timezone.utc)

        return await self.user_repository.update(
            user.id,
            phone_verified_at=verified_at,
        )

    async def update_last_login(
        self,
        user: User,
    ) -> User:
        return await self.user_repository.update_last_login(
            user.id
        )
