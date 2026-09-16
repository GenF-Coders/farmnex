from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm import Farm


class FarmRepository:
    """
    Database repository for Farm.

    Responsibilities:
        - Farm database queries
        - Farm persistence

    This repository does NOT:
        - commit transactions
        - rollback transactions
        - enforce authorization
        - enforce HTTP/API rules
        - decide whether a user is allowed to access a farm
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ================================================================
    # READ
    # ================================================================

    async def get_by_id(
        self,
        farm_id: int,
    ) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.id == farm_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.public_id == public_id
            )
        )

        return result.scalar_one_or_none()

    async def get_user_farm(
        self,
        *,
        user_id: int,
        farm_name: str,
    ) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.user_id == user_id,
                func.lower(Farm.farm_name)
                == farm_name.strip().lower(),
            )
        )

        return result.scalar_one_or_none()

    async def get_user_farm_by_public_id(
        self,
        *,
        user_id: int,
        public_id: UUID,
    ) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.user_id == user_id,
                Farm.public_id == public_id,
            )
        )

        return result.scalar_one_or_none()

    # ================================================================
    # LIST
    # ================================================================

    async def list_by_user_id(
        self,
        *,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Farm]:
        result = await self.db.execute(
            select(Farm)
            .where(
                Farm.user_id == user_id
            )
            .order_by(
                Farm.created_at.desc(),
                Farm.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    # ================================================================
    # EXISTS
    # ================================================================

    async def exists(
        self,
        farm_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(Farm.id)
            .where(
                Farm.id == farm_id
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_by_public_id(
        self,
        public_id: UUID,
    ) -> bool:
        result = await self.db.execute(
            select(Farm.id)
            .where(
                Farm.public_id == public_id
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_for_user(
        self,
        *,
        user_id: int,
        farm_name: str,
        exclude_id: int | None = None,
    ) -> bool:
        query = select(Farm.id).where(
            Farm.user_id == user_id,
            func.lower(Farm.farm_name)
            == farm_name.strip().lower(),
        )

        if exclude_id is not None:
            query = query.where(
                Farm.id != exclude_id
            )

        result = await self.db.execute(
            query.limit(1)
        )

        return result.scalar_one_or_none() is not None

    # ================================================================
    # CREATE
    # ================================================================

    async def create(
        self,
        **values: Any,
    ) -> Farm:
        farm = Farm(**values)

        self.db.add(farm)

        await self.db.flush()
        await self.db.refresh(farm)

        return farm

    # ================================================================
    # UPDATE
    # ================================================================

    async def update(
        self,
        farm: Farm,
        **values: Any,
    ) -> Farm | None:
        if farm is None:
            return None

        allowed_fields = {
            "farm_name",
            "description",
            "address_line_1",
            "address_line_2",
            "landmark",
            "village",
            "city",
            "district",
            "state",
            "postal_code",
            "country",
            "latitude",
            "longitude",
            "is_active",
            "farm_file_path",
            "farm_file_content_type",
        }

        for field, value in values.items():
            if field in allowed_fields:
                setattr(
                    farm,
                    field,
                    value,
                )

        await self.db.flush()
        await self.db.refresh(farm)

        return farm

    # ================================================================
    # FILE
    # ================================================================

    async def update_file(
        self,
        farm: Farm,
        *,
        file_path: str,
        content_type: str,
    ) -> Farm | None:
        return await self.update(
            farm,
            farm_file_path=file_path,
            farm_file_content_type=content_type,
        )

    async def clear_file(
        self,
        farm: Farm,
    ) -> Farm | None:
        return await self.update(
            farm,
            farm_file_path=None,
            farm_file_content_type=None,
        )

    # ================================================================
    # DELETE
    # ================================================================

    async def delete(
        self,
        farm: Farm,
    ) -> bool:
        if farm is None:
            return False

        await self.db.delete(farm)
        await self.db.flush()

        return True

    async def delete_by_id(
        self,
        farm_id: int,
    ) -> bool:
        farm = await self.get_by_id(farm_id)

        if farm is None:
            return False

        return await self.delete(farm)

    async def delete_by_public_id(
        self,
        public_id: UUID,
    ) -> bool:
        farm = await self.get_by_public_id(
            public_id
        )

        if farm is None:
            return False

        return await self.delete(farm)

    # ================================================================
    # COUNT
    # ================================================================

    async def count_by_user_id(
        self,
        user_id: int,
    ) -> int:
        result = await self.db.execute(
            select(func.count(Farm.id))
            .where(
                Farm.user_id == user_id
            )
        )

        return int(result.scalar_one())

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count(Farm.id))
        )

        return int(result.scalar_one())