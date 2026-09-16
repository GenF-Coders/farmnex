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
    StorageNotFoundError,
    StorageProviderError,
    StorageService,
    StorageValidationError,
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

    PROFILE_IMAGE_FOLDER = "profile_image"

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
    def _role_name(
        user: User,
    ) -> str | None:
        role = getattr(user, "role", None)

        if role is None:
            return None

        name = getattr(role, "name", None)

        if name is None:
            return None

        return str(name).upper()

    @staticmethod
    def _storage_bucket() -> str:
        bucket = getattr(
            settings,
            "storage_bucket",
            None,
        )

        if not isinstance(bucket, str) or not bucket.strip():
            raise ConflictError(
                "Storage bucket is not configured."
            )

        return bucket.strip()

    @classmethod
    def _profile_image_path(
        cls,
        *,
        content_type: str,
    ) -> str:
        """
        Generate the canonical FarmNex profile-image path.

        Result:

            profile_image/<uuid>.jpg
            profile_image/<uuid>.png
            profile_image/<uuid>.webp

        No user ID is placed in the path.
        """

        normalized = content_type.strip().lower()

        if normalized not in cls.PROFILE_IMAGE_CONTENT_TYPES:
            raise ValidationError(
                "Only JPEG, PNG, and WebP profile images are allowed."
            )

        if cls.storage_service_for_path is None:
            raise ConflictError(
                "Storage service is not configured."
            )

        return cls.storage_service_for_path.build_uuid_path(
            folder=cls.PROFILE_IMAGE_FOLDER,
            content_type=normalized,
        )

    @classmethod
    def _validate_profile_image_path(
        cls,
        path: str,
    ) -> str:
        """
        Validate an existing profile-image database reference.

        Only:

            profile_image/<filename>

        is accepted.
        """

        if not isinstance(path, str) or not path.strip():
            raise ConflictError(
                "Profile image storage reference is invalid."
            )

        value = path.strip()

        parts = value.split("/")

        if (
            len(parts) != 2
            or parts[0] != cls.PROFILE_IMAGE_FOLDER
        ):
            raise ConflictError(
                "Profile image storage reference is invalid."
            )

        if cls.storage_service_for_path is None:
            raise ConflictError(
                "Storage service is not configured."
            )

        try:
            return cls.storage_service_for_path.validate_managed_path(
                value
            )
        except StorageValidationError as exc:
            raise ConflictError(
                "Profile image storage reference is invalid."
            ) from exc

    # This class-level reference is used only by the path helper.
    # The instance is assigned during __init__.
    storage_service_for_path: StorageService | None = None

    # ============================================================
    # INITIALIZATION HOOK
    # ============================================================

    def _set_storage_service_reference(self) -> None:
        self.__class__.storage_service_for_path = self.storage_service

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
        """
        Upload or replace the authenticated user's profile image.

        Storage lifecycle:

            validate
                ↓
            upload new object
                ↓
            update DB reference
                ↓
            best-effort delete old object
                ↓
            generate signed URL
        """

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

        # Make sure the instance-level storage reference used by
        # the path helper is current.
        self.__class__.storage_service_for_path = (
            self.storage_service
        )

        try:
            normalized_content_type = (
                self.storage_service.validate_file(
                    file_bytes=file_bytes,
                    content_type=normalized_content_type,
                    verify_signature=True,
                )
            )
        except StorageValidationError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        # StorageService is now responsible for generating the
        # canonical flat-folder UUID path.
        new_path = self._profile_image_path(
            content_type=normalized_content_type,
        )

        old_path = user.profile_image_path

        if old_path:
            self._validate_profile_image_path(
                old_path
            )

        # --------------------------------------------------------
        # Upload new object
        # --------------------------------------------------------

        try:
            await self.storage_service.upload(
                bucket=self._storage_bucket(),
                path=new_path,
                file_bytes=file_bytes,
                content_type=normalized_content_type,
                upsert=False,
                verify_signature=False,
            )

        except StorageValidationError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        except StorageProviderError:
            # Keep the original storage exception so the controller
            # can return the correct 503 storage response.
            raise

        except StorageError:
            raise

        # --------------------------------------------------------
        # Persist new DB reference
        # --------------------------------------------------------

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
            # Database update failed after storage upload.
            # Remove the newly uploaded object to avoid an orphan.
            try:
                await self.storage_service.delete(
                    bucket=self._storage_bucket(),
                    path=new_path,
                )
            except StorageError:
                pass

            raise

        # --------------------------------------------------------
        # Cleanup old object
        # --------------------------------------------------------

        if (
            old_path
            and old_path != new_path
        ):
            try:
                await self.storage_service.delete(
                    bucket=self._storage_bucket(),
                    path=old_path,
                )

            except StorageNotFoundError:
                pass

            except StorageError:
                # DB already points to the new object.
                # Do not make a successful replacement look like
                # a failed request because old-object cleanup failed.
                pass

        # --------------------------------------------------------
        # Generate signed URL
        # --------------------------------------------------------

        try:
            image_url = await self.storage_service.create_signed_url(
                bucket=self._storage_bucket(),
                path=new_path,
                expires_in=settings.storage_signed_url_expire_seconds,
            )

        except StorageNotFoundError as exc:
            raise ConflictError(
                "Profile image was uploaded, but the stored object "
                "could not be found."
            ) from exc

        except StorageProviderError:
            raise

        except StorageError:
            raise

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

        self.__class__.storage_service_for_path = (
            self.storage_service
        )

        path = self._validate_profile_image_path(
            path
        )

        try:
            return await self.storage_service.create_signed_url(
                bucket=self._storage_bucket(),
                path=path,
                expires_in=settings.storage_signed_url_expire_seconds,
            )

        except StorageNotFoundError as exc:
            raise ResourceNotFoundError(
                "Profile image was not found in storage."
            ) from exc

        except StorageProviderError:
            raise

        except StorageValidationError as exc:
            raise ConflictError(
                "Profile image storage reference is invalid."
            ) from exc

        except StorageError:
            raise

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

        self.__class__.storage_service_for_path = (
            self.storage_service
        )

        path = self._validate_profile_image_path(
            path
        )

        # Clear DB reference first.
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

        # Then remove storage object.
        try:
            await self.storage_service.delete(
                bucket=self._storage_bucket(),
                path=path,
            )

        except StorageNotFoundError:
            # DB reference is already cleared and object is already absent.
            return

        except StorageProviderError as exc:
            raise ConflictError(
                "Profile image reference was removed, but the "
                "storage object could not be deleted."
            ) from exc

        except StorageError as exc:
            raise ConflictError(
                "Profile image reference was removed, but the "
                "storage object could not be deleted."
            ) from exc