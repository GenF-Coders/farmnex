from __future__ import annotations

from uuid import UUID

from app.models.role import Role
from app.repositories.role_repository import RoleRepository


class RoleService:
    def __init__(
        self,
        role_repository: RoleRepository,
    ) -> None:
        self.role_repository = role_repository

    async def get_by_id(self, role_id: int) -> Role | None:
        return await self.role_repository.get_by_id(role_id)

    async def get_by_public_id(self, public_id: UUID) -> Role | None:
        return await self.role_repository.get_by_public_id(public_id)

    async def get_by_name(self, name: str) -> Role | None:
        return await self.role_repository.get_by_name(name)

    async def exists_by_name(self, name: str) -> bool:
        return await self.role_repository.exists_by_name(name)

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Role]:
        return await self.role_repository.get_all(
            offset=offset,
            limit=limit,
        )

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Role:
        name = name.strip().upper()

        existing_role = await self.role_repository.get_by_name(name)

        if existing_role is not None:
            raise ValueError("Role with this name already exists.")

        return await self.role_repository.create(
            name=name,
            description=description,
        )

    async def update(
        self,
        role: Role,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Role:
        values: dict[str, object] = {}

        if name is not None and name.strip().upper() != role.name:
            normalized_name = name.strip().upper()
            existing_role = await self.role_repository.get_by_name(
                normalized_name
            )

            if existing_role is not None:
                raise ValueError(
                    "Role with this name already exists."
                )

            values["name"] = normalized_name

        if description is not None:
            values["description"] = description

        if not values:
            return role

        return await self.role_repository.update(
            role.id,
            **values,
        )

    async def delete(self, role: Role) -> None:
        await self.role_repository.delete(role.id)
