from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.role_repository import RoleRepository
from app.services.role_service import RoleService
from app.schemas.role import RoleResponse


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


def get_role_service(
    db: AsyncSession = Depends(get_db),
) -> RoleService:
    role_repository = RoleRepository(db)

    return RoleService(
        role_repository=role_repository,
    )


# ============================================================
# CREATE
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_role(
    role_service: RoleService = Depends(get_role_service),
):
    """
    Create a new role.

    This should be ADMIN-only.
    """
    raise NotImplementedError


# ============================================================
# READ
# ============================================================

@router.get("", response_model=list[RoleResponse])
async def get_roles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    role_service: RoleService = Depends(get_role_service),
):
    """
    Get available roles.
    """
    return await role_service.get_all(
        offset=skip,
        limit=limit,
    )


@router.get("/{public_id}", response_model=RoleResponse)
async def get_role(
    public_id: UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """
    Get a role by public UUID.
    """
    role = await role_service.get_by_public_id(public_id)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found.",
        )

    return role


# ============================================================
# UPDATE
# ============================================================

@router.patch("/{public_id}")
async def update_role(
    public_id: UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """
    Update role name/description.

    This should be ADMIN-only.
    """
    raise NotImplementedError


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_role(
    public_id: UUID,
    role_service: RoleService = Depends(get_role_service),
):
    """
    Delete a role.

    Service layer must prevent deletion if users are still
    assigned to the role.
    """
    raise NotImplementedError


# ============================================================
# USERS ASSIGNED TO ROLE
# ============================================================

@router.get("/{public_id}/users")
async def get_role_users(
    public_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    role_service: RoleService = Depends(get_role_service),
):
    """
    Get users assigned to a particular role.

    This will eventually require RoleRepository/UserRepository
    support for querying users by role.
    """
    raise NotImplementedError