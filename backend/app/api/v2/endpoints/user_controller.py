from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import (
    MessageResponse,
    ProfileImageResponse,
    ProfileImageUrlResponse,
    RoleResponse,
    UserProfileUpdateRequest,
    UserResponse,
)
from app.services.exceptions import (
    ConflictError,
    ForbiddenOperationError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.storage_service import storage_service
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


# ============================================================
# DEPENDENCIES
# ============================================================


def get_user_service(
    db: AsyncSession = Depends(get_db),
) -> UserService:
    """
    Build UserService for the current request.

    StorageService is a shared singleton because storage
    configuration/client state is application-wide.
    """

    return UserService(
        user_repository=UserRepository(db),
        role_repository=RoleRepository(db),
        storage_service=storage_service,
    )


# ============================================================
# RESPONSE BUILDER
# ============================================================


async def _build_user_response(
    *,
    user: User,
    service: UserService,
) -> UserResponse:
    """
    Convert User ORM object into the public API response.

    profile_image_path is an internal storage reference and is
    never exposed to the client.

    A signed URL is generated only when an image actually exists.
    """

    profile_image_url: str | None = None

    if user.profile_image_path:
        profile_image_url = (
            await service.get_profile_image_url(
                current_user=user,
            )
        )

    role = user.role

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User role could not be loaded.",
        )

    return UserResponse(
        public_id=user.public_id,
        phone_number=user.phone_number,
        phone_verified_at=user.phone_verified_at,
        first_name=user.first_name,
        middle_name=user.middle_name,
        surname=user.surname,
        alternate_phone_number=user.alternate_phone_number,
        alternate_phone_verified_at=(
            user.alternate_phone_verified_at
        ),
        date_of_birth=user.date_of_birth,
        gender=user.gender,
        profile_image_url=profile_image_url,
        preferred_language=user.preferred_language,
        timezone=user.timezone,
        occupation=user.occupation,
        bio=user.bio,
        role=RoleResponse(
            public_id=role.public_id,
            name=role.name,
            description=role.description,
            created_at=role.created_at,
            updated_at=role.updated_at,
        ),
        account_status=(
            user.account_status.value
            if hasattr(user.account_status, "value")
            else str(user.account_status)
        ),
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


# ============================================================
# EXCEPTION TRANSLATION
# ============================================================


def _service_exception_to_http(
    exc: Exception,
) -> HTTPException:
    """
    Translate application/service exceptions into HTTP errors.
    """

    if isinstance(
        exc,
        ResourceNotFoundError,
    ):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ResourceAlreadyExistsError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ConflictError,
    ):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ForbiddenOperationError,
    ):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(
        exc,
        ValidationError,
    ):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to complete the requested operation.",
    )


# ============================================================
# GET CURRENT USER
# ============================================================


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my user profile",
)
async def get_my_user(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Return the authenticated user's complete profile.
    """

    try:
        user = await service.get_my_profile(
            current_user=current_user,
        )

        return await _build_user_response(
            user=user,
            service=service,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(exc) from exc


# ============================================================
# UPDATE CURRENT USER PROFILE
# ============================================================


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update my profile",
)
async def update_my_user(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Update generic profile fields for the authenticated user.
    """

    try:
        user = await service.update_profile(
            current_user=current_user,
            profile_data=payload.model_dump(
                exclude_unset=True,
            ),
        )

        return await _build_user_response(
            user=user,
            service=service,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(exc) from exc


# ============================================================
# PROFILE IMAGE - UPLOAD / REPLACE
# ============================================================


@router.post(
    "/me/image",
    response_model=ProfileImageResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload or replace my profile image",
)
async def upload_my_profile_image(
    file: Annotated[
        UploadFile,
        File(
            description=(
                "JPEG, PNG, or WebP profile image."
            ),
        ),
    ],
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> ProfileImageResponse:
    """
    Upload or replace the authenticated user's profile image.
    """

    content_type = (
        file.content_type or ""
    ).strip().lower()

    allowed_content_types = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    if content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Only JPEG, PNG, and WebP "
                "profile images are allowed."
            ),
        )

    max_size = settings.storage_max_upload_size_bytes

    try:
        file_bytes = await file.read(
            max_size + 1,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read the uploaded file.",
        ) from exc

    finally:
        await file.close()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Profile image cannot be empty.",
        )

    if len(file_bytes) > max_size:
        limit_mb = max_size / (
            1024 * 1024
        )

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "Profile image exceeds the maximum "
                f"upload size of {limit_mb:g} MB."
            ),
        )

    try:
        user, image_url = (
            await service.upload_profile_image(
                current_user=current_user,
                file_bytes=file_bytes,
                content_type=content_type,
            )
        )

        return ProfileImageResponse(
            user=await _build_user_response(
                user=user,
                service=service,
            ),
            profile_image_url=image_url,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(exc) from exc


# ============================================================
# PROFILE IMAGE - GET SIGNED URL
# ============================================================


@router.get(
    "/me/image",
    response_model=ProfileImageUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get my profile image URL",
)
async def get_my_profile_image_url(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> ProfileImageUrlResponse:
    """
    Generate a temporary signed URL for the private
    profile image.
    """

    try:
        image_url = await service.get_profile_image_url(
            current_user=current_user,
        )

        return ProfileImageUrlResponse(
            profile_image_url=image_url,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(exc) from exc


# ============================================================
# PROFILE IMAGE - DELETE
# ============================================================


@router.delete(
    "/me/image",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete my profile image",
)
async def delete_my_profile_image(
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> MessageResponse:
    """
    Delete the authenticated user's profile image.
    """

    try:
        await service.delete_profile_image(
            current_user=current_user,
        )

        return MessageResponse(
            message="Profile image deleted successfully.",
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(exc) from exc


# ============================================================
# ADMIN / INTERNAL USER LOOKUP
# ============================================================


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List users",
)
async def list_users(
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of users to skip.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
        description="Maximum number of users to return.",
    ),
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """
    List users for privileged roles.
    """

    role_name = getattr(
        getattr(current_user, "role", None),
        "name",
        None,
    )

    if str(role_name).upper() not in {
        "SUPER_ADMIN",
        "ADMIN",
        "MANAGER",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not permitted to list users.",
        )

    try:
        users = await service.get_all(
            offset=offset,
            limit=limit,
        )

        responses: list[UserResponse] = []

        for user in users:
            responses.append(
                await _build_user_response(
                    user=user,
                    service=service,
                )
            )

        return responses

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(exc) from exc


# ============================================================
# GET USER BY PUBLIC UUID
# ============================================================


@router.get(
    "/{user_public_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by public ID",
)
async def get_user(
    user_public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Get another user by public UUID.

    Restricted to privileged roles.
    """

    role_name = getattr(
        getattr(current_user, "role", None),
        "name",
        None,
    )

    if str(role_name).upper() not in {
        "SUPER_ADMIN",
        "ADMIN",
        "MANAGER",
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not permitted to view another user.",
        )

    try:
        user = await service.get_by_public_id(
            user_public_id,
        )

        if user is None:
            raise ResourceNotFoundError(
                "User not found.",
            )

        return await _build_user_response(
            user=user,
            service=service,
        )

    except HTTPException:
        raise

    except Exception as exc:
        raise _service_exception_to_http(exc) from exc