from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address


class AddressRepository:
    """
    Database repository for Address.

    No authorization or business rules belong here.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ============================================================
    # READ
    # ============================================================

    async def get_by_id(
        self,
        address_id: int,
    ) -> Address | None:
        result = await self.db.execute(
            select(Address).where(
                Address.id == address_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> Address | None:
        result = await self.db.execute(
            select(Address).where(
                Address.public_id == public_id
            )
        )
        return result.scalar_one_or_none()

    async def get_user_address(
        self,
        *,
        user_id: int,
        address_id: int,
    ) -> Address | None:
        result = await self.db.execute(
            select(Address).where(
                Address.id == address_id,
                Address.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def get_user_address_by_public_id(
        self,
        *,
        user_id: int,
        public_id: UUID,
    ) -> Address | None:
        result = await self.db.execute(
            select(Address).where(
                Address.public_id == public_id,
                Address.user_id == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def list_by_user_id(
        self,
        *,
        user_id: int,
        active_only: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Address]:
        query = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(
                Address.is_default.desc(),
                Address.created_at.desc(),
                Address.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )

        if active_only:
            query = query.where(
                Address.is_active.is_(True)
            )

        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def list_active_by_user_id(
        self,
        *,
        user_id: int,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Address]:
        return await self.list_by_user_id(
            user_id=user_id,
            active_only=True,
            offset=offset,
            limit=limit,
        )

    async def get_default_by_user_id(
        self,
        user_id: int,
    ) -> Address | None:
        result = await self.db.execute(
            select(Address).where(
                Address.user_id == user_id,
                Address.is_default.is_(True),
                Address.is_active.is_(True),
            )
        )

        return result.scalar_one_or_none()

    # ============================================================
    # EXISTS
    # ============================================================

    async def exists(
        self,
        address_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(Address.id)
            .where(Address.id == address_id)
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def exists_for_user(
        self,
        *,
        user_id: int,
        address_id: int,
    ) -> bool:
        result = await self.db.execute(
            select(Address.id)
            .where(
                Address.id == address_id,
                Address.user_id == user_id,
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
    ) -> Address:
        address = Address(**values)

        self.db.add(address)

        await self.db.flush()
        await self.db.refresh(address)

        return address

    # ============================================================
    # UPDATE
    # ============================================================

    async def update(
        self,
        address: Address,
        **values: Any,
    ) -> Address | None:
        if address is None:
            return None

        allowed_fields = {
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
            "is_default",
            "is_active",
        }

        for field, value in values.items():
            if field in allowed_fields:
                setattr(address, field, value)

        await self.db.flush()
        await self.db.refresh(address)

        return address

    # ============================================================
    # DEFAULT ADDRESS
    # ============================================================

    async def clear_default_for_user(
        self,
        *,
        user_id: int,
        exclude_address_id: int | None = None,
    ) -> int:
        query = (
            update(Address)
            .where(
                Address.user_id == user_id,
                Address.is_default.is_(True),
            )
            .values(is_default=False)
        )

        if exclude_address_id is not None:
            query = query.where(
                Address.id != exclude_address_id
            )

        result = await self.db.execute(query)

        await self.db.flush()

        return int(result.rowcount or 0)

    async def set_default(
        self,
        address: Address,
    ) -> Address | None:
        if address is None:
            return None

        address.is_default = True

        await self.db.flush()
        await self.db.refresh(address)

        return address

    async def clear_default(
        self,
        address: Address,
    ) -> Address | None:
        if address is None:
            return None

        address.is_default = False

        await self.db.flush()
        await self.db.refresh(address)

        return address

    # ============================================================
    # STATUS
    # ============================================================

    async def deactivate(
        self,
        address: Address,
    ) -> Address | None:
        if address is None:
            return None

        address.is_active = False
        address.is_default = False

        await self.db.flush()
        await self.db.refresh(address)

        return address

    async def activate(
        self,
        address: Address,
    ) -> Address | None:
        if address is None:
            return None

        address.is_active = True

        await self.db.flush()
        await self.db.refresh(address)

        return address

    # ============================================================
    # DELETE
    # ============================================================

    async def delete(
        self,
        address: Address,
    ) -> bool:
        if address is None:
            return False

        await self.db.delete(address)
        await self.db.flush()

        return True

    async def delete_by_id(
        self,
        address_id: int,
    ) -> bool:
        address = await self.get_by_id(address_id)

        if address is None:
            return False

        return await self.delete(address)

    # ============================================================
    # COUNT
    # ============================================================

    async def count_by_user_id(
        self,
        *,
        user_id: int,
        active_only: bool = False,
    ) -> int:
        query = select(
            func.count(Address.id)
        ).where(
            Address.user_id == user_id
        )

        if active_only:
            query = query.where(
                Address.is_active.is_(True)
            )

        result = await self.db.execute(query)

        return int(result.scalar_one())

    async def count(self) -> int:
        result = await self.db.execute(
            select(func.count(Address.id))
        )

        return int(result.scalar_one())