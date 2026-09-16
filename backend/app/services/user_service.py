from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from app.core.config import settings
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
from app.services.storage_service import (
    StorageError,
    StorageProviderError,
    StorageValidationError,
    StorageService,
)


class UserService:
    """
    Business/application service for users.

    Responsibilities:
        - user creation
        - profile management
        - account management
        - role validation
        - phone validation/business rules
        - alternate phone rules
        - profile image lifecycle
        - user lookup

    Transaction rule:
        This service does not commit or rollback.

    The controller/application transaction boundary owns commit/rollback.

    Security rule:
        Client-provided ownership/system fields are never trusted.
    """

    PROFILE_IMAGE_CONTENT_TYPES = frozenset(
        {
            "image/jpeg",
            "image/png",
            "image/webp",
        }
    )

    PROFILE_IMAGE_PREFIX = "users"

    # Generic profile fields that a normal authenticated user may edit.
    PROFILE_UPDATE_FIELDS = frozenset(
        {
            "first_name",
            "middle_name",
            "surname",
            "alternate_phone_number",
            "date_of_birth",
            "gender",
            "preferred_language",
            "timezone",
            "occupation",
            "bio",
        }
    )

    # Fields that must never be accepted through generic user/profile
    # create/update requests.
    PROTECTED_FIELDS = frozenset(
        {
            "id",
            "public_id",
            "role_id",
            "account_status",
            "pin_hash",
            "phone_number",
            "phone_verified_at",
            "alternate_phone_verified_at",
            "profile_image_path",
            "last_login_at",
            "created_at",
            "updated_at",
        }
    )

    def __init__(
        self,
        user_repository: UserRepository,
        role_repository: RoleRepository,
        storage_service: StorageService | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.role_repository = role_repository
        self.storage_service = storage_service

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _normalize_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    @classmethod
    def _clean_profile_data(
        cls,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Accept flexible frontend data while allowing only supported
        editable profile fields.

        Unknown fields are ignored.

        Protected fields are ignored.

        None remains meaningful for nullable fields.
        """
        cleaned: dict[str, Any] = {}

        for key, value in data.items():
            if key not in cls.PROFILE_UPDATE_FIELDS:
                continue

            if isinstance(value, str):
                value = cls._normalize_text(value)

            cleaned[key] = value

        return cleaned

    @staticmethod
    def _validate_date_of_birth(
        value: date | None,
    ) -> None:
        if value is None:
            return

        if value > date.today():
            raise ValidationError(
                "Date of birth cannot be in the future."
            )

    @staticmethod
    def _normalize_phone(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value

    @staticmethod
    def _role_name(user: User) -> str | None:
        role = getattr(user, "role", None)

        if role is None:
            return None

        name = getattr(role, "name", None)

        if name is None:
            return None

        return str(name).upper()

    @staticmethod
    def _storage_bucket() -> str:
        bucket = settings.storage_bucket

        if not isinstance(bucket, str) or not bucket.strip():
            raise ConflictError(
                "Storage bucket is not configured."
            )

        return bucket.strip()

    @classmethod
    def _profile_image_prefix(
        cls,
        user_public_id: UUID,
    ) -> str:
        return (
            f"{cls.PROFILE_IMAGE_PREFIX}/"
            f"{user_public_id}/profile/"
        )

    @classmethod
    def _profile_image_path(
        cls,
        *,
        user_public_id: UUID,
        content_type: str,
    ) -> str:
        extension_map = {
            "image/jpeg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }

        extension = extension_map.get(
            content_type.strip().lower()
        )

        if extension is None:
            raise ValidationError(
                "Only JPEG, PNG, and WebP profile images are allowed."
            )

        from uuid import uuid4

        return (
            f"{cls._profile_image_prefix(user_public_id)}"
            f"{uuid4()}.{extension}"
        )

    # ============================================================
    # READ
    # ============================================================

    async def get_by_id(
        self,
        user_id: int,
    ) -> User | None:
        return await self.user_repository.get_by_id(
            user_id
        )

    async def get_by_public_id(
        self,
        public_id: UUID,
    ) -> User | None:
        return await self.user_repository.get_by_public_id(
            public_id
        )

    async def get_by_phone(
        self,
        phone_number: str,
    ) -> User | None:
        phone_number = self._normalize_phone(
            phone_number
        )

        if phone_number is None:
            return None

        return await self.user_repository.get_by_phone(
            phone_number
        )

    async def get_by_phone_with_role(
        self,
        phone_number: str,
    ) -> User | None:
        phone_number = self._normalize_phone(
            phone_number
        )

        if phone_number is None:
            return None

        return await self.user_repository.get_by_phone_with_role(
            phone_number
        )

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        if offset < 0:
            raise ValidationError(
                "Offset cannot be negative."
            )

        if limit < 1 or limit > 100:
            raise ValidationError(
                "Limit must be between 1 and 100."
            )

        return await self.user_repository.get_all(
            offset=offset,
            limit=limit,
        )

    # ============================================================
    # EXISTENCE
    # ============================================================

    async def exists_by_phone(
        self,
        phone_number: str,
    ) -> bool:
        phone_number = self._normalize_phone(
            phone_number
        )

        if phone_number is None:
            return False

        return await self.user_repository.exists_by_phone(
            phone_number
        )

    async def exists_by_alternate_phone(
        self,
        alternate_phone_number: str,
        *,
        exclude_user_id: int | None = None,
    ) -> bool:
        phone = self._normalize_phone(
            alternate_phone_number
        )

        if phone is None:
            return False

        return await self.user_repository.exists_by_alternate_phone(
            phone,
            exclude_user_id=exclude_user_id,
        )

    # ============================================================
    # CREATE
    # ============================================================

    async def create(
        self,
        *,
        phone_number: str,
        role_id: int,
        user_data: dict[str, Any] | None = None,
        pin_hash: str | None = None,
        phone_verified_at: datetime | None = None,
        account_status: AccountStatus = AccountStatus.ACTIVE,
    ) -> User:
        """
        Create a user.

        `user_data` may contain arbitrary frontend data.

        Only supported profile columns are accepted from it.

        Authentication/system fields are controlled by this service.
        """
        phone_number = self._normalize_phone(
            phone_number
        )

        if phone_number is None:
            raise ValidationError(
                "Phone number is required."
            )

        existing_user = await self.user_repository.get_by_phone(
            phone_number
        )

        if existing_user is not None:
            raise ResourceAlreadyExistsError(
                "User with this phone number already exists."
            )

        role = await self.role_repository.get_by_id(
            role_id
        )

        if role is None:
            raise ResourceNotFoundError(
                "Role not found."
            )

        profile_data = self._clean_profile_data(
            user_data or {}
        )

        if "date_of_birth" in profile_data:
            self._validate_date_of_birth(
                profile_data["date_of_birth"]
            )

        alternate_phone = profile_data.get(
            "alternate_phone_number"
        )

        if alternate_phone == phone_number:
            raise ValidationError(
                "Alternate phone number cannot be the same as "
                "the primary phone number."
            )

        if alternate_phone:
            already_used = (
                await self.user_repository
                .exists_by_alternate_phone(
                    alternate_phone
                )
            )

            if already_used:
                raise ResourceAlreadyExistsError(
                    "This alternate phone number is already in use."
                )

        try:
            return await self.user_repository.create(
                phone_number=phone_number,
                role_id=role.id,
                pin_hash=pin_hash,
                phone_verified_at=phone_verified_at,
                account_status=account_status,
                alternate_phone_verified_at=None,
                **profile_data,
            )
        except ResourceAlreadyExistsError:
            raise
        except Exception as exc:
            raise ConflictError(
                "Unable to create user."
            ) from exc

    async def create_with_role_name(
        self,
        *,
        phone_number: str,
        role_name: str,
        user_data: dict[str, Any] | None = None,
        phone_verified_at: datetime | None = None,
    ) -> User:
        role_name = self._normalize_text(
            role_name
        )

        if role_name is None:
            raise ValidationError(
                "Role is required."
            )

        role = await self.role_repository.get_by_name(
            role_name
        )

        if role is None:
            raise ResourceNotFoundError(
                f"Role '{role_name}' is not available."
            )

        return await self.create(
            phone_number=phone_number,
            role_id=role.id,
            user_data=user_data,
            phone_verified_at=phone_verified_at,
            account_status=AccountStatus.ACTIVE,
        )

    # ============================================================
    # PROFILE
    # ============================================================

    async def get_my_profile(
        self,
        *,
        current_user: User,
    ) -> User:
        """
        Profile is now part of User.

        No separate Profile table is used.
        """
        user = await self.user_repository.get_by_id(
            current_user.id
        )

        if user is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        return user

    async def update_profile(
        self,
        *,
        current_user: User,
        profile_data: dict[str, Any],
    ) -> User:
        """
        Update generic profile information.

        Business rules:
            - system fields cannot be changed
            - primary phone cannot be changed here
            - role cannot be changed here
            - account status cannot be changed here
            - alternate phone verification resets when number changes
            - alternate phone cannot equal primary phone
            - alternate phone must be unique
        """
        updates = self._clean_profile_data(
            profile_data
        )

        if not updates:
            return await self.get_my_profile(
                current_user=current_user
            )

        if "date_of_birth" in updates:
            self._validate_date_of_birth(
                updates["date_of_birth"]
            )

        if "alternate_phone_number" in updates:
            new_phone = self._normalize_phone(
                updates["alternate_phone_number"]
            )

            if new_phone == current_user.phone_number:
                raise ValidationError(
                    "Alternate phone number cannot be the same "
                    "as the primary phone number."
                )

            current_alternate = (
                current_user.alternate_phone_number
            )

            if new_phone != current_alternate:
                if new_phone is not None:
                    already_used = (
                        await self.user_repository
                        .exists_by_alternate_phone(
                            new_phone,
                            exclude_user_id=current_user.id,
                        )
                    )

                    if already_used:
                        raise ResourceAlreadyExistsError(
                            "This alternate phone number is already in use."
                        )

                updates[
                    "alternate_phone_number"
                ] = new_phone

                updates[
                    "alternate_phone_verified_at"
                ] = None

        try:
            updated = await self.user_repository.update_profile(
                current_user,
                updates,
            )
        except ResourceAlreadyExistsError:
            raise
        except Exception as exc:
            raise ConflictError(
                "Unable to update user profile."
            ) from exc

        if updated is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        return updated

    # ============================================================
    # PHONE / ACCOUNT
    # ============================================================

    async def mark_phone_verified(
        self,
        user: User,
    ) -> User:
        verified_at = datetime.now(
            timezone.utc
        )

        updated = await self.user_repository.update(
            user.id,
            phone_verified_at=verified_at,
        )

        if updated is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        return updated

    async def update_last_login(
        self,
        user: User,
    ) -> User:
        updated = await self.user_repository.update_last_login(
            user.id
        )

        if updated is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        return updated

    async def update_role(
        self,
        user: User,
        role_id: int,
    ) -> User:
        role = await self.role_repository.get_by_id(
            role_id
        )

        if role is None:
            raise ResourceNotFoundError(
                "Role not found."
            )

        updated = await self.user_repository.update_role(
            user.id,
            role.id,
        )

        if updated is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        return updated

    async def update_pin(
        self,
        user: User,
        pin_hash: str,
    ) -> User:
        if not pin_hash or not pin_hash.strip():
            raise ValidationError(
                "PIN hash cannot be empty."
            )

        updated = await self.user_repository.update_pin_hash(
            user.id,
            pin_hash,
        )

        if updated is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        return updated

    async def change_account_status(
        self,
        user: User,
        status: AccountStatus,
    ) -> User:
        updated = (
            await self.user_repository
            .update_account_status(
                user.id,
                status,
            )
        )

        if updated is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        return updated

    # ============================================================
    # PROFILE IMAGE
    # ============================================================

    async def upload_profile_image(
        self,
        *,
        current_user: User,
        file_bytes: bytes,
        content_type: str,
    ) -> tuple[User, str]:
        if self.storage_service is None:
            raise ConflictError(
                "Storage service is not configured."
            )

        user = await self.get_my_profile(
            current_user=current_user
        )

        normalized_content_type = (
            content_type or ""
        ).strip().lower()

        if normalized_content_type not in (
            self.PROFILE_IMAGE_CONTENT_TYPES
        ):
            raise ValidationError(
                "Only JPEG, PNG, and WebP profile images are allowed."
            )

        try:
            normalized_content_type = (
                self.storage_service.validate_file(
                    file_bytes=file_bytes,
                    content_type=normalized_content_type,
                )
            )
        except StorageValidationError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        new_path = self._profile_image_path(
            user_public_id=user.public_id,
            content_type=normalized_content_type,
        )

        old_path = user.profile_image_path

        try:
            await self.storage_service.upload(
                bucket=self._storage_bucket(),
                path=new_path,
                file_bytes=file_bytes,
                content_type=normalized_content_type,
            )
        except StorageValidationError as exc:
            raise ValidationError(
                str(exc)
            ) from exc
        except StorageProviderError as exc:
            raise ConflictError(
                "Unable to upload profile image."
            ) from exc
        except StorageError as exc:
            raise ConflictError(
                "Profile image upload failed."
            ) from exc

        try:
            updated_user = (
                await self.user_repository
                .update_profile_image(
                    user.id,
                    new_path,
                )
            )

            if updated_user is None:
                raise ResourceNotFoundError(
                    "User not found."
                )

        except Exception:
            try:
                await self.storage_service.delete(
                    bucket=self._storage_bucket(),
                    path=new_path,
                )
            except StorageError:
                pass

            raise

        # Old object is deleted only after DB references the new object.
        if old_path and old_path != new_path:
            try:
                await self.storage_service.delete(
                    bucket=self._storage_bucket(),
                    path=old_path,
                )
            except StorageError:
                # The database already points to the correct object.
                pass

        # The repository has already returned the updated User object.
        # Generate the URL directly from the new, server-generated path so
        # this upload request does not depend on a second profile lookup.
        try:
            image_url = await self.storage_service.create_signed_url(
                bucket=self._storage_bucket(),
                path=new_path,
                expires_in=settings.storage_signed_url_expire_seconds,
            )
        except StorageProviderError as exc:
            raise ConflictError(
                "Unable to generate profile image URL."
            ) from exc
        except StorageError as exc:
            raise ConflictError(
                "Unable to access profile image."
            ) from exc

        return updated_user, image_url

    async def get_profile_image_url(
        self,
        *,
        current_user: User,
    ) -> str:
        if self.storage_service is None:
            raise ConflictError(
                "Storage service is not configured."
            )

        user = await self.get_my_profile(
            current_user=current_user
        )

        path = user.profile_image_path

        if not path:
            raise ResourceNotFoundError(
                "Profile image not found."
            )

        expected_prefix = self._profile_image_prefix(
            user.public_id
        )

        if not path.startswith(expected_prefix):
            raise ConflictError(
                "Profile image storage reference is invalid."
            )

        try:
            return await self.storage_service.create_signed_url(
                bucket=self._storage_bucket(),
                path=path,
                expires_in=settings.storage_signed_url_expire_seconds,
            )
        except StorageProviderError as exc:
            raise ConflictError(
                "Unable to generate profile image URL."
            ) from exc
        except StorageError as exc:
            raise ConflictError(
                "Unable to access profile image."
            ) from exc


    async def delete_profile_image(
        self,
        *,
        current_user: User,
    ) -> None:
        if self.storage_service is None:
            raise ConflictError(
                "Storage service is not configured."
            )

        user = await self.get_my_profile(
            current_user=current_user
        )

        path = user.profile_image_path

        if not path:
            raise ResourceNotFoundError(
                "Profile image not found."
            )

        expected_prefix = self._profile_image_prefix(
            user.public_id
        )

        if not path.startswith(expected_prefix):
            raise ConflictError(
                "Profile image storage reference is invalid."
            )

        updated_user = (
            await self.user_repository
            .clear_profile_image(
                user.id
            )
        )

        if updated_user is None:
            raise ResourceNotFoundError(
                "User not found."
            )

        try:
            await self.storage_service.delete(
                bucket=self._storage_bucket(),
                path=path,
            )
        except StorageError as exc:
            raise ConflictError(
                "Profile image reference was removed, but the "
                "storage object could not be deleted."
            ) from exc