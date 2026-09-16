from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm import Farm


class FarmRepository:
    """
    Database repository for Farm.

    Ownership/business rules remain in FarmService.
    The repository only performs database operations.
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        self.db = db

    # ============================================================
    # READ
    # ============================================================

    async def get_by_id(
        self,
        farm_id: int,
    ) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.id == farm_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.public_id == public_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_user_farm(
        self,
        *,
        user_id: int,
        farm_name: str | None = None,
        farm_id: int | None = None,
    ) -> Farm | None:
        query = select(Farm).where(
            Farm.user_id == user_id,
        )

        if farm_id is not None:
            query = query.where(
                Farm.id == farm_id,
            )

        if farm_name is not None:
            query = query.where(
                func.lower(Farm.farm_name)
                == farm_name.strip().lower(),
            )

        result = await self.db.execute(query)

        return result.scalar_one_or_none()

    async def get_user_farm_by_public_id(
        self,
        *,
        user_id: int,
        public_id: UUID,
    ) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(
                Farm.public_id == public_id,
                Farm.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_user_id(
        self,
        *,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Farm]:
        result = await self.db.execute(
            select(Farm)
            .where(
                Farm.user_id == user_id,
            )
            .order_by(
                Farm.created_at.desc(),
                Farm.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        return list(result.scalars().all())

    # ============================================================
    # EXISTS
    # ============================================================

    async def exists(
        self,
        farm_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(Farm.id)
            .where(
                Farm.id == farm_id,
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
                Farm.public_id == public_id,
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_for_user(
        self,
        *,
        user_id: int,
        farm_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(Farm.id)
            .where(
                Farm.id == farm_id,
                Farm.user_id == user_id,
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    # ============================================================
    # CREATE
    # ============================================================

    async def create(
        self,
        **values: Any,
    ) -> Farm:
        farm = Farm(
            **values,
        )

        self.db.add(farm)

        await self.db.flush()
        await self.db.refresh(farm)

        return farm

    # ============================================================
    # UPDATE
    # ============================================================

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

    # ============================================================
    # FARM FILE
    # ============================================================

    async def update_file(
        self,
        farm: Farm,
        *,
        farm_file_path: str,
        farm_file_content_type: str,
    ) -> Farm | None:
        if farm is None:
            return None

        farm.farm_file_path = farm_file_path
        farm.farm_file_content_type = (
            farm_file_content_type
        )

        await self.db.flush()
        await self.db.refresh(farm)

        return farm

    async def clear_file(
        self,
        farm: Farm,
    ) -> Farm | None:
        if farm is None:
            return None

        farm.farm_file_path = None
        farm.farm_file_content_type = None

        await self.db.flush()
        await self.db.refresh(farm)

        return farm

    # ============================================================
    # DELETE
    # ============================================================

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
        farm = await self.get_by_id(
            farm_id,
        )

        if farm is None:
            return False

        return await self.delete(
            farm,
        )

    async def delete_by_public_id(
        self,
        public_id: UUID,
    ) -> bool:
        farm = await self.get_by_public_id(
            public_id,
        )

        if farm is None:
            return False

        return await self.delete(
            farm,
        )

    # ============================================================
    # COUNT
    # ============================================================

    async def count_by_user_id(
        self,
        user_id: int,
    ) -> int:
        result = await self.db.execute(
            select(
                func.count(Farm.id)
            ).where(
                Farm.user_id == user_id,
            )
        )

        return int(
            result.scalar_one()
        )

    async def count(self) -> int:
        result = await self.db.execute(
            select(
                func.count(Farm.id)
            )
        )

        return int(
            result.scalar_one()
        )