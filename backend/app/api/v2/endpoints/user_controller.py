from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    user_repository = UserRepository(db)
    role_repository = RoleRepository(db)

    return UserService(
        user_repository=user_repository,
        role_repository=role_repository,
    )


# ============================================================
# CREATE
# ============================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_service: UserService = Depends(get_user_service),
):
    """
    Create a new user.

    Business validation and role validation should be handled
    by UserService.
    """
    raise NotImplementedError


# ============================================================
# READ
# ============================================================

@router.get("")
async def get_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get paginated users.

    This endpoint should normally be restricted to admins.
    """
    raise NotImplementedError


@router.get("/{public_id}")
async def get_user(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a user by public UUID.
    """
    user = await user_service.get_by_public_id(public_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


@router.get("/{public_id}/role")
async def get_user_role(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get the role assigned to a user.
    """
    user = await user_service.get_by_public_id(public_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user.role


# ============================================================
# UPDATE
# ============================================================

@router.patch("/{public_id}")
async def update_user(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update editable user information.

    Do NOT allow sensitive fields such as role, account_status,
    or pin_hash to be modified through this generic endpoint.
    """
    raise NotImplementedError


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{public_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Permanently delete a user.

    In production, prefer disabling/suspending an account unless
    permanent deletion is genuinely required.
    """
    raise NotImplementedError


# ============================================================
# ROLE MANAGEMENT
# ============================================================

@router.patch("/{public_id}/role")
async def update_user_role(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Change a user's role.

    This must be ADMIN-only.
    """
    raise NotImplementedError


# ============================================================
# ACCOUNT STATUS
# ============================================================

@router.patch("/{public_id}/status")
async def update_user_status(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Change account status.

    This must be ADMIN-only.
    """
    raise NotImplementedError


@router.post("/{public_id}/activate")
async def activate_user(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Activate a suspended/disabled user.

    This must be ADMIN-only.
    """
    raise NotImplementedError


@router.post("/{public_id}/suspend")
async def suspend_user(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Suspend a user.

    This must be ADMIN-only.
    """
    raise NotImplementedError


@router.post("/{public_id}/disable")
async def disable_user(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Permanently/administratively disable a user.

    This must be ADMIN-only.
    """
    raise NotImplementedError


# ============================================================
# PHONE VERIFICATION
# ============================================================

@router.post("/{public_id}/verify-phone")
async def verify_user_phone(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Mark the user's phone number as verified.

    Actual OTP verification should happen in AuthService.
    """
    raise NotImplementedError


# ============================================================
# PIN
# ============================================================

@router.patch("/{public_id}/pin")
async def update_user_pin(
    public_id: UUID,
    user_service: UserService = Depends(get_user_service),
):
    """
    Change/set the user's PIN.

    Never accept or return pin_hash directly.
    """
    raise NotImplementedError