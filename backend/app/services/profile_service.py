from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.models.profile import Profile
from app.models.user import User
from app.repositories.profile_repository import ProfileRepository
from app.services.exceptions import (
    ConflictError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    ValidationError,
)
from app.services.storage.exceptions import (
    StorageError,
    StorageProviderError,
    StorageValidationError,
)
from app.services.storage_service import storage_service


class ProfileService:
    """
    Business/application service for user profiles.

    Responsibilities:
        - Profile ownership
        - Profile lifecycle
        - Profile validation/business rules
        - Profile-image storage lifecycle
        - Signed profile-image URLs

    Transaction rule:
        This service does not commit/rollback the database session.
        The API dependency/controller transaction boundary should own
        the actual commit/rollback.
    """

    PROFILE_STORAGE_PREFIX = "users"

    def __init__(
        self,
        *,
        profile_repository: ProfileRepository,
    ) -> None:
        self.profile_repository = profile_repository

    # ============================================================
    # INTERNAL HELPERS
    # ============================================================

    @staticmethod
    def _profile_image_prefix(user_public_id: UUID) -> str:
        return (
            f"{ProfileService.PROFILE_STORAGE_PREFIX}/"
            f"{user_public_id}/profile/"
        )

    @classmethod
    def _build_profile_image_path(
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

        return (
            f"{cls._profile_image_prefix(user_public_id)}"
            f"{uuid4()}.{extension}"
        )

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    # ============================================================
    # READ
    # ============================================================

    async def get_my_profile(
        self,
        *,
        current_user: User,
    ) -> Profile:
        profile = await self.profile_repository.get_by_user_id(
            current_user.id
        )

        if profile is None:
            raise ResourceNotFoundError(
                "Profile not found."
            )

        return profile

    # ============================================================
    # CREATE
    # ============================================================

    async def create_profile(
        self,
        *,
        current_user: User,
        profile_data: dict,
    ) -> Profile:
        existing = await self.profile_repository.get_by_user_id(
            current_user.id
        )

        if existing is not None:
            raise ResourceAlreadyExistsError(
                "Profile already exists."
            )

        cleaned_data = {
            key: self._normalize_text(value)
            if isinstance(value, str)
            else value
            for key, value in profile_data.items()
        }

        # Never trust caller-provided ownership fields.
        cleaned_data.pop("id", None)
        cleaned_data.pop("public_id", None)
        cleaned_data.pop("user_id", None)
        cleaned_data.pop("profile_image_path", None)

        try:
            profile = await self.profile_repository.create(
                public_id=uuid4(),
                user_id=current_user.id,
                **cleaned_data,
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to create profile."
            ) from exc

        return profile

    # ============================================================
    # UPDATE
    # ============================================================

    async def update_profile(
        self,
        *,
        current_user: User,
        profile_data: dict,
    ) -> Profile:
        profile = await self.get_my_profile(
            current_user=current_user
        )

        updates = dict(profile_data)

        # Ownership/system fields are never client-editable.
        protected_fields = {
            "id",
            "public_id",
            "user_id",
            "profile_image_path",
            "alternate_phone_verified_at",
            "created_at",
            "updated_at",
        }

        for field in protected_fields:
            updates.pop(field, None)

        if not updates:
            return profile

        for key, value in updates.items():
            if isinstance(value, str):
                updates[key] = self._normalize_text(value)

        # Alternate phone verification must be reset whenever
        # the alternate phone number changes.
        if "alternate_phone_number" in updates:
            new_phone = updates["alternate_phone_number"]

            current_phone = profile.alternate_phone_number

            if new_phone != current_phone:
                updates["alternate_phone_verified_at"] = None

        try:
            updated_profile = await self.profile_repository.update(
                profile,
                updates,
            )
        except Exception as exc:
            raise ConflictError(
                "Unable to update profile."
            ) from exc

        if updated_profile is None:
            raise ResourceNotFoundError(
                "Profile not found."
            )

        return updated_profile

    # ============================================================
    # DELETE
    # ============================================================

    async def delete_profile(
        self,
        *,
        current_user: User,
    ) -> None:
        profile = await self.get_my_profile(
            current_user=current_user
        )

        image_path = profile.profile_image_path

        deleted = await self.profile_repository.delete(
            profile
        )

        if not deleted:
            raise ResourceNotFoundError(
                "Profile not found."
            )

        # Storage is external to the DB transaction.
        # If storage deletion fails, do not make the API pretend
        # the storage object definitely disappeared.
        if image_path:
            try:
                await storage_service.delete(
                    path=image_path
                )
            except StorageProviderError as exc:
                raise ConflictError(
                    "Profile was deleted, but the profile image "
                    "could not be removed from storage."
                ) from exc
            except StorageError as exc:
                raise ConflictError(
                    "Profile was deleted, but profile-image cleanup "
                    "failed."
                ) from exc

    # ============================================================
    # PROFILE IMAGE
    # ============================================================

    async def upload_profile_image(
        self,
        *,
        current_user: User,
        file_bytes: bytes,
        content_type: str,
    ) -> tuple[Profile, str]:
        profile = await self.get_my_profile(
            current_user=current_user
        )

        normalized_content_type = (
            content_type or ""
        ).strip().lower()

        if not file_bytes:
            raise ValidationError(
                "Profile image cannot be empty."
            )

        try:
            normalized_content_type = (
                storage_service.validate_image(
                    content_type=normalized_content_type,
                    size_bytes=len(file_bytes),
                )
            )
        except StorageValidationError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        new_path = self._build_profile_image_path(
            user_public_id=current_user.public_id,
            content_type=normalized_content_type,
        )

        old_path = profile.profile_image_path

        try:
            await storage_service.upload(
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
            updated_profile = (
                await self.profile_repository.update_profile_image(
                    profile,
                    new_path,
                )
            )

            if updated_profile is None:
                raise ResourceNotFoundError(
                    "Profile not found."
                )

        except Exception:
            # Database update failed after storage upload.
            # Remove the newly-created orphan object.
            try:
                await storage_service.delete(
                    path=new_path
                )
            except StorageError:
                # Do not hide the original DB error.
                pass

            raise

        # Remove old image only after the new DB reference exists.
        if old_path and old_path != new_path:
            try:
                await storage_service.delete(
                    path=old_path
                )
            except StorageError:
                # The database now points to the correct new image.
                # Do not roll back the profile just because old
                # object cleanup failed.
                pass

        signed_url = await self.get_profile_image_url(
            current_user=current_user,
            profile=updated_profile,
        )

        return updated_profile, signed_url

    async def get_profile_image_url(
        self,
        *,
        current_user: User,
        profile: Profile | None = None,
    ) -> str:
        if profile is None:
            profile = await self.get_my_profile(
                current_user=current_user
            )

        path = profile.profile_image_path

        if not path:
            raise ResourceNotFoundError(
                "Profile image not found."
            )

        expected_prefix = self._profile_image_prefix(
            current_user.public_id
        )

        if not path.startswith(expected_prefix):
            raise ConflictError(
                "Profile image storage reference is invalid."
            )

        try:
            return await storage_service.create_signed_url(
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
        profile = await self.get_my_profile(
            current_user=current_user
        )

        path = profile.profile_image_path

        if not path:
            raise ResourceNotFoundError(
                "Profile image not found."
            )

        expected_prefix = self._profile_image_prefix(
            current_user.public_id
        )

        if not path.startswith(expected_prefix):
            raise ConflictError(
                "Profile image storage reference is invalid."
            )

        # Clear DB reference first.
        updated_profile = (
            await self.profile_repository.clear_profile_image(
                profile
            )
        )

        if updated_profile is None:
            raise ResourceNotFoundError(
                "Profile not found."
            )

        try:
            await storage_service.delete(
                path=path
            )
        except StorageError as exc:
            # DB no longer references the image, so the image is now
            # an orphan. It can be cleaned asynchronously later.
            raise ConflictError(
                "Profile image reference was removed, but the "
                "storage object could not be deleted."
            ) from exc