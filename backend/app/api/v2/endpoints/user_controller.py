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
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.enums import AccountStatus
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.exceptions import (
    ConflictError,
    ForbiddenOperationError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.storage_service import StorageService
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

    UserService owns:
        - user/profile business rules
        - role validation
        - alternate-phone rules
        - profile-image lifecycle
    """
    return UserService(
        user_repository=UserRepository(db),
        role_repository=RoleRepository(db),
        storage_service=StorageService(),
    )


# ============================================================
# RESPONSE SCHEMAS
# ============================================================


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class UserResponse(BaseModel):
    """
    Public representation of the authenticated user.

    Internal database ID, PIN hash and other sensitive fields
    are intentionally never exposed.
    """

    model_config = ConfigDict(from_attributes=True)

    public_id: UUID

    # Authentication/account information
    phone_number: str
    phone_verified_at: datetime | None

    # Generic profile information
    first_name: str | None = None
    middle_name: str | None = None
    surname: str | None = None

    alternate_phone_number: str | None = None
    alternate_phone_verified_at: datetime | None = None

    date_of_birth: date | None
    gender: str | None

    profile_image_url: str | None

    preferred_language: str | None = None
    timezone: str | None = None
    occupation: str | None = None
    bio: str | None = None

    # Account information
    role: RoleResponse
    account_status: str

    created_at: datetime
    updated_at: datetime
    last_login_at: object | None


class ProfileImageResponse(BaseModel):
    """
    Response returned after profile-image upload.
    """

    user: UserResponse
    profile_image_url: str


class ProfileImageUrlResponse(BaseModel):
    profile_image_url: str


class MessageResponse(BaseModel):
    message: str


# ============================================================
# REQUEST SCHEMAS
# ============================================================


class UserProfileUpdateRequest(BaseModel):
    """
    Generic authenticated-user profile update.

    IMPORTANT:
    Authentication/system fields are deliberately absent.

    The UserService performs the final business-level whitelist
    and ignores unknown/protected fields.
    """

    model_config = ConfigDict(
        extra="ignore",
    )

    first_name: str | None = Field(
        default=None,
        max_length=100,
    )

    middle_name: str | None = Field(
        default=None,
        max_length=100,
    )

    surname: str | None = Field(
        default=None,
        max_length=100,
    )

    alternate_phone_number: str | None = Field(
        default=None,
        max_length=20,
    )

    date_of_birth: date | None = None

    gender: str | None = Field(
        default=None,
        max_length=30,
    )

    preferred_language: str | None = Field(
        default=None,
        max_length=20,
    )

    timezone: str | None = Field(
        default=None,
        max_length=50,
    )

    occupation: str | None = Field(
        default=None,
        max_length=150,
    )

    bio: str | None = Field(
        default=None,
        max_length=5000,
    )


# ============================================================
# RESPONSE BUILDERS
# ============================================================


async def _build_user_response(
    *,
    user: User,
    service: UserService,
) -> UserResponse:
    """
    Convert User ORM object into the public API representation.

    profile_image_path is an internal storage reference and is
    never exposed directly.

    A signed URL is generated only when an image exists.
    """

    profile_image_url: str | None = None

    if user.profile_image_path:
        profile_image_url = await service.get_profile_image_url(
            current_user=user,
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
        alternate_phone_verified_at=user.alternate_phone_verified_at,
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
    Translate application/service exceptions into HTTP responses.

    Controllers translate errors.
    Services remain independent of FastAPI.
    """

    if isinstance(exc, ResourceNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    if isinstance(exc, ResourceAlreadyExistsError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, ConflictError):
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    if isinstance(exc, ForbiddenOperationError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    if isinstance(exc, ValidationError):
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unable to complete the requested operation.",
    )


# ============================================================
# CURRENT USER
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
    Return the authenticated user's complete user/profile record.
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

    Primary phone number, role, account status, PIN and verification
    fields cannot be changed through this endpoint.

    Primary-phone changes should have their own OTP-protected flow.
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
# PROFILE IMAGE - UPLOAD
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
            description="JPEG, PNG, or WebP profile image.",
        ),
    ],
    current_user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
) -> ProfileImageResponse:
    """
    Upload a profile image.

    The storage path is generated entirely by UserService.
    The client never controls the storage path.
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
            detail="Only JPEG, PNG, and WebP profile images are allowed.",
        )

    max_size = settings.storage_max_upload_size_bytes

    try:
        # Read one byte beyond the configured limit so an oversized
        # upload can be rejected without accepting arbitrary amounts
        # of data into memory.
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
        limit_mb = max_size / (1024 * 1024)

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"Profile image exceeds the maximum "
                f"upload size of {limit_mb:g} MB."
            ),
        )

    try:
        user, image_url = await service.upload_profile_image(
            current_user=current_user,
            file_bytes=file_bytes,
            content_type=content_type,
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
    Generate a short-lived signed URL for the authenticated
    user's private profile image.
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
    Remove the authenticated user's profile image.

    The database reference is cleared before storage cleanup,
    as implemented by UserService.
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
    List users.

    NOTE:
    This endpoint is currently authentication-protected but should
    receive role-based authorization before being exposed to normal
    customers/farmers.

    Keep authorization in a dedicated authorization dependency rather
    than silently allowing every authenticated user to enumerate users.
    """

    # Until role-based authorization dependencies are introduced,
    # prevent this endpoint from being accidentally exposed to
    # ordinary users.
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
    Get a user by public UUID.

    This endpoint is restricted to privileged roles.
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