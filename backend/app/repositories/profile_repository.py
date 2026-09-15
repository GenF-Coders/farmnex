from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile


class ProfileRepository:
    """
    Database repository for Profile.

    Responsibilities:
        - Profile queries
        - Profile persistence
        - Profile deletion

    This repository does NOT:
        - commit transactions
        - rollback transactions
        - enforce HTTP/API rules
        - enforce authorization

    Transaction ownership belongs to the service/controller layer.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ============================================================
    # READ
    # ============================================================

    async def get_by_id(
        self,
        profile_id: int,
    ) -> Profile | None:
        result = await self.db.execute(
            select(Profile).where(
                Profile.id == profile_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> Profile | None:
        result = await self.db.execute(
            select(Profile).where(
                Profile.public_id == public_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: int,
    ) -> Profile | None:
        result = await self.db.execute(
            select(Profile).where(
                Profile.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    # ============================================================
    # EXISTS
    # ============================================================

    async def exists(
        self,
        profile_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(Profile.id)
            .where(Profile.id == profile_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_public_id(
        self,
        public_id: UUID,
    ) -> bool:
        result = await self.db.execute(
            select(Profile.id)
            .where(Profile.public_id == public_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_user_id(
        self,
        user_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(Profile.id)
            .where(Profile.user_id == user_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    # ============================================================
    # CREATE
    # ============================================================

    async def create(
        self,
        **values: Any,
    ) -> Profile:
        profile = Profile(**values)

        self.db.add(profile)

        await self.db.flush()
        await self.db.refresh(profile)

        return profile

    # ============================================================
    # UPDATE
    # ============================================================

    async def update(
        self,
        profile: Profile,
        values: dict[str, Any],
    ) -> Profile | None:
        """
        Update only fields explicitly present in `values`.

        `None` is meaningful and can therefore clear nullable
        database columns.
        """

        if profile is None:
            return None

        allowed_fields = {
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

        for field, value in values.items():
            if field in allowed_fields:
                setattr(profile, field, value)

        await self.db.flush()
        await self.db.refresh(profile)

        return profile

    async def update_profile_image(
        self,
        profile: Profile,
        profile_image_path: str,
    ) -> Profile | None:
        if profile is None:
            return None

        profile.profile_image_path = profile_image_path

        await self.db.flush()
        await self.db.refresh(profile)

        return profile

    async def clear_profile_image(
        self,
        profile: Profile,
    ) -> Profile | None:
        if profile is None:
            return None

        profile.profile_image_path = None

        await self.db.flush()
        await self.db.refresh(profile)

        return profile

    # ============================================================
    # DELETE
    # ============================================================

    async def delete(
        self,
        profile: Profile,
    ) -> bool:
        if profile is None:
            return False

        await self.db.delete(profile)
        await self.db.flush()

        return True

    async def delete_by_id(
        self,
        profile_id: int,
    ) -> bool:
        profile = await self.get_by_id(profile_id)

        if profile is None:
            return False

        return await self.delete(profile)

    async def delete_by_user_id(
        self,
        user_id: int,
    ) -> bool:
        result = await self.db.execute(
            delete(Profile).where(
                Profile.user_id == user_id
            )
        )

        await self.db.flush()

        return result.rowcount > 0

    # ============================================================
    # COUNT
    # ============================================================

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count(Profile.id))
        )

        return int(result.scalar_one())