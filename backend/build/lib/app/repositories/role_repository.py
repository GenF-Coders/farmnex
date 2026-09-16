from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        public_id: UUID | None = None,
    ) -> Role:
        role = Role(name=name, description=description)
        if public_id is not None:
            role.public_id = public_id
        self.session.add(role)
        await self.session.flush()
        return role

    async def get_by_id(self, role_id: int) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.id == role_id)
        )
        return result.scalar_one_or_none()

    async def get_by_public_id(self, public_id: UUID) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Role | None:
        result = await self.session.execute(
            select(Role).where(Role.name == name.strip().upper())
        )
        return result.scalar_one_or_none()

    async def get_all(self, *, offset: int = 0, limit: int = 100) -> list[Role]:
        result = await self.session.execute(
            select(Role).order_by(Role.id.asc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def exists_by_id(self, role_id: int) -> bool:
        result = await self.session.execute(
            select(Role.id).where(Role.id == role_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def exists_by_name(self, name: str) -> bool:
        return await self.get_by_name(name) is not None

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(Role.id)))
        return int(result.scalar_one())

    async def update(self, role_id: int, **values) -> Role | None:
        await self.session.execute(
            update(Role).where(Role.id == role_id).values(**values)
        )
        await self.session.flush()
        return await self.get_by_id(role_id)

    async def update_name(self, role_id: int, name: str) -> Role | None:
        return await self.update(role_id, name=name.strip().upper())

    async def delete(self, role_id: int) -> bool:
        result = await self.session.execute(
            delete(Role).where(Role.id == role_id)
        )
        await self.session.flush()
        return result.rowcount > 0
