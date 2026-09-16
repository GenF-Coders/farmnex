from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    """
    Database repository for User.

    Responsibilities:
        - User queries
        - User persistence
        - User profile persistence
        - User authentication/account persistence

    This repository does NOT:
        - commit transactions
        - rollback transactions
        - enforce HTTP/API rules
        - enforce authorization
        - decide whether a caller is allowed to perform an operation

    The service layer owns business and authorization decisions.

    Important:
        create/update accept flexible keyword data, but only explicitly
        whitelisted model fields are persisted. This prevents arbitrary
        frontend keys from modifying protected database fields.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ============================================================
    # FIELD DEFINITIONS
    # ============================================================

    # Fields that may be supplied when creating a user.
    #
    # Protected/generated fields such as id/public_id/timestamps are
    # intentionally not part of the normal create contract.
    CREATE_FIELDS = frozenset(
        {
            "phone_number",
            "phone_verified_at",
            "pin_hash",
            "role_id",
            "account_status",
            "first_name",
            "middle_name",
            "surname",
            "alternate_phone_number",
            "alternate_phone_verified_at",
            "date_of_birth",
            "gender",
            "profile_image_path",
            "preferred_language",
            "timezone",
            "occupation",
            "bio",
        }
    )

    # Generic profile update fields.
    #
    # Authentication, authorization, identity and account-state fields
    # are intentionally excluded.
    PROFILE_UPDATE_FIELDS = frozenset(
        {
            "first_name",
            "middle_name",
            "surname",
            "alternate_phone_number",
            "date_of_birth",
            "gender",
            "preferred_language",
            "timezone",
            "occupation",
            "bio",
        }
    )

    # Authentication/account fields that have dedicated repository
    # methods below.
    AUTH_UPDATE_FIELDS = frozenset(
        {
            "phone_number",
            "phone_verified_at",
            "pin_hash",
            "role_id",
            "account_status",
            "last_login_at",
            "alternate_phone_number",
            "alternate_phone_verified_at",
        }
    )

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _filter_values(
        values: dict[str, Any],
        allowed_fields: frozenset[str],
    ) -> dict[str, Any]:
        """
        Return only explicitly allowed model fields.

        Unknown frontend fields are ignored rather than blindly passed
        to SQLAlchemy.

        `None` is preserved because None can intentionally clear a
        nullable database column.
        """
        return {
            field: value
            for field, value in values.items()
            if field in allowed_fields
        }

    # ============================================================
    # READ
    # ============================================================

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.id == user_id)
        )

        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.public_id == public_id)
        )

        return result.scalar_one_or_none()

    async def get_by_phone(
        self,
        phone_number: str,
    ) -> User | None:
        result = await self.db.execute(
            select(User).where(
                User.phone_number == phone_number
            )
        )

        return result.scalar_one_or_none()

    async def get_by_phone_with_role(
        self,
        phone_number: str,
    ) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .where(User.phone_number == phone_number)
        )

        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.role))
            .order_by(
                User.created_at.desc(),
                User.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    # ============================================================
    # EXISTS
    # ============================================================

    async def exists_by_id(
        self,
        user_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(User.id)
            .where(User.id == user_id)
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_by_public_id(
        self,
        public_id: UUID,
    ) -> bool:
        result = await self.db.execute(
            select(User.id)
            .where(User.public_id == public_id)
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_by_phone(
        self,
        phone_number: str,
    ) -> bool:
        result = await self.db.execute(
            select(User.id)
            .where(User.phone_number == phone_number)
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_by_alternate_phone(
        self,
        alternate_phone_number: str,
        *,
        exclude_user_id: int | None = None,
    ) -> bool:
        query = (
            select(User.id)
            .where(
                User.alternate_phone_number
                == alternate_phone_number
            )
            .limit(1)
        )

        if exclude_user_id is not None:
            query = query.where(
                User.id != exclude_user_id
            )

        result = await self.db.execute(query)

        return result.scalar_one_or_none() is not None

    # ============================================================
    # CREATE
    # ============================================================

    async def create(
        self,
        **values: Any,
    ) -> User:
        """
        Create a User using only supported creation fields.

        Unknown keys are ignored.

        Example:

            await repository.create(
                phone_number="+919876543210",
                role_id=1,
                first_name="John",
                surname="Doe",
                some_frontend_field="ignored",
            )
        """
        filtered_values = self._filter_values(
            values,
            self.CREATE_FIELDS,
        )

        user = User(**filtered_values)

        self.db.add(user)

        await self.db.flush()
        await self.db.refresh(user)

        return user

    # ============================================================
    # GENERIC PROFILE UPDATE
    # ============================================================

    async def update_profile(
        self,
        user: User,
        values: dict[str, Any],
    ) -> User | None:
        """
        Update only allowed generic profile fields.

        Fields explicitly supplied with None are allowed to clear
        nullable profile columns.

        Protected fields are ignored.
        """
        if user is None:
            return None

        filtered_values = self._filter_values(
            values,
            self.PROFILE_UPDATE_FIELDS,
        )

        if not filtered_values:
            return user

        for field, value in filtered_values.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)

        return user

    # ============================================================
    # GENERIC SAFE UPDATE
    # ============================================================

    async def update(
        self,
        user_id: int,
        **values: Any,
    ) -> User | None:
        """
        Generic safe update.

        Only authentication/account fields and profile fields that are
        explicitly supported by this repository are accepted.

        Identity/generated fields are never writable here.
        """
        allowed_fields = (
            self.PROFILE_UPDATE_FIELDS
            | self.AUTH_UPDATE_FIELDS
        )

        filtered_values = self._filter_values(
            values,
            allowed_fields,
        )

        if not filtered_values:
            return await self.get_by_id(user_id)

        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**filtered_values)
        )

        await self.db.flush()

        return await self.get_by_id(user_id)

    # ============================================================
    # LAST LOGIN
    # ============================================================

    async def update_last_login(
        self,
        user_id: int,
    ) -> User | None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=func.now())
        )

        await self.db.flush()

        return await self.get_by_id(user_id)

    # ============================================================
    # PHONE
    # ============================================================

    async def update_phone(
        self,
        user_id: int,
        phone_number: str,
        phone_verified_at: datetime | None = None,
    ) -> User | None:
        return await self.update(
            user_id,
            phone_number=phone_number,
            phone_verified_at=phone_verified_at,
        )

    # ============================================================
    # ALTERNATE PHONE
    # ============================================================

    async def update_alternate_phone(
        self,
        user_id: int,
        alternate_phone_number: str | None,
        alternate_phone_verified_at: datetime | None = None,
    ) -> User | None:
        return await self.update(
            user_id,
            alternate_phone_number=alternate_phone_number,
            alternate_phone_verified_at=alternate_phone_verified_at,
        )

    # ============================================================
    # PIN
    # ============================================================

    async def update_pin_hash(
        self,
        user_id: int,
        pin_hash: str | None,
    ) -> User | None:
        return await self.update(
            user_id,
            pin_hash=pin_hash,
        )

    # ============================================================
    # ROLE
    # ============================================================

    async def update_role(
        self,
        user_id: int,
        role_id: int,
    ) -> User | None:
        return await self.update(
            user_id,
            role_id=role_id,
        )

    # ============================================================
    # ACCOUNT STATUS
    # ============================================================

    async def update_account_status(
        self,
        user_id: int,
        account_status: Any,
    ) -> User | None:
        return await self.update(
            user_id,
            account_status=account_status,
        )

    # ============================================================
    # PROFILE IMAGE
    # ============================================================

    async def update_profile_image(
        self,
        user_id: int,
        profile_image_path: str,
    ) -> User | None:
        """
        Persist a profile image path through the dedicated image API.

        profile_image_path is intentionally NOT part of the generic profile
        update whitelist. This method is the only repository operation used
        by the UserService image lifecycle.
        """
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(profile_image_path=profile_image_path)
        )

        if not result.rowcount:
            return None

        await self.db.flush()
        return await self.get_by_id(user_id)

    async def clear_profile_image(
        self,
        user_id: int,
    ) -> User | None:
        """
        Clear the profile image reference through the dedicated image API.
        """
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(profile_image_path=None)
        )

        if not result.rowcount:
            return None

        await self.db.flush()
        return await self.get_by_id(user_id)

    # ============================================================
    # DELETE
    # ============================================================

    async def delete(
        self,
        user_id: int,
    ) -> bool:
        result = await self.db.execute(
            delete(User).where(
                User.id == user_id
            )
        )

        await self.db.flush()

        return bool(result.rowcount)

    # ============================================================
    # COUNT
    # ============================================================

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count(User.id))
        )

        return int(result.scalar_one())