from uuid import UUID, uuid4

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError
from app.models.farm import Farm
from app.repositories.farm_repository import FarmRepository
from app.services.storage_service import (
    StorageError,
    StorageValidationError,
    storage_service,
)


class FarmService:
    def __init__(self, repository: FarmRepository):
        self.repository = repository
        self.storage_service = storage_service

    async def create_farm(
        self,
        user_id: int,
        farm_data: dict,
    ) -> Farm:
        farm_name = farm_data.get("farm_name")

        if await self.repository.exists_for_user(
            user_id=user_id,
            farm_name=farm_name,
        ):
            raise ConflictError(
                "You already have a farm with this name."
            )

        farm_data["user_id"] = user_id

        return await self.repository.create(farm_data)

    async def get_farm(
        self,
        user_id: int,
        farm_public_id: UUID,
    ) -> Farm:
        farm = await self.repository.get_user_farm_by_public_id(
            user_id=user_id,
            public_id=farm_public_id,
        )

        if not farm:
            raise NotFoundError("Farm not found.")

        return farm

    async def list_farms(
        self,
        user_id: int,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Farm], int]:
        farms = await self.repository.list_by_user_id(
            user_id=user_id,
            offset=offset,
            limit=limit,
        )

        total = await self.repository.count_by_user_id(user_id)

        return farms, total

    async def update_farm(
        self,
        user_id: int,
        farm_public_id: UUID,
        farm_data: dict,
    ) -> Farm:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        farm_name = farm_data.get("farm_name")

        if (
            farm_name
            and farm_name.lower() != farm.farm_name.lower()
            and await self.repository.exists_for_user(
                user_id=user_id,
                farm_name=farm_name,
                exclude_id=farm.id,
            )
        ):
            raise ConflictError(
                "You already have a farm with this name."
            )

        return await self.repository.update(
            farm.id,
            farm_data,
        )

    async def delete_farm(
        self,
        user_id: int,
        farm_public_id: UUID,
    ) -> None:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        old_path = farm.farm_file_path

        await self.repository.delete(farm.id)

        if old_path:
            try:
                await self.storage_service.delete(
                    bucket=settings.storage_bucket,
                    path=old_path,
                )
            except StorageError:
                # DB deletion has already succeeded.
                # Storage cleanup is intentionally best effort.
                pass

    # ------------------------------------------------------------------
    # Farm file
    # ------------------------------------------------------------------

    def _build_farm_file_path(
        self,
        content_type: str,
    ) -> str:
        extension = self.storage_service.extension_for_content_type(
            content_type
        )

        return self.storage_service.build_path(
            folder="farm-files",
            filename=f"{uuid4()}.{extension}",
        )

    def _validate_file(
        self,
        file_bytes: bytes,
        content_type: str,
        filename: str | None,
    ) -> None:
        self.storage_service.validate_file(
            file_bytes=file_bytes,
            content_type=content_type,
            filename=filename,
            verify_signature=True,
        )

    def _validate_stored_path(
        self,
        path: str,
    ) -> None:
        self.storage_service.validate_managed_path(path)

    async def upload_farm_file(
        self,
        user_id: int,
        farm_public_id: UUID,
        file_bytes: bytes,
        content_type: str,
        filename: str | None = None,
    ) -> tuple[str, str]:
        """
        Upload a new farm file or replace the existing one.

        DB stores only the storage path.
        API returns a fresh signed URL.
        """

        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        normalized_content_type = (
            self.storage_service.normalize_content_type(content_type)
        )

        self._validate_file(
            file_bytes=file_bytes,
            content_type=normalized_content_type,
            filename=filename,
        )

        bucket = settings.storage_bucket

        new_path = self._build_farm_file_path(
            normalized_content_type
        )

        old_path = farm.farm_file_path

        # Upload the new object first.
        await self.storage_service.upload(
            bucket=bucket,
            path=new_path,
            file_bytes=file_bytes,
            content_type=normalized_content_type,
        )

        try:
            # Generate the signed URL before changing DB state.
            signed_url, _expires = (
                await self.storage_service.create_signed_url(
                    bucket=bucket,
                    path=new_path,
                )
            )

            # Store ONLY the permanent storage path.
            await self.repository.update_file(
                farm.id,
                file_path=new_path,
                content_type=normalized_content_type,
            )

        except Exception:
            # If DB update or URL generation fails,
            # remove the newly uploaded object.
            try:
                await self.storage_service.delete(
                    bucket=bucket,
                    path=new_path,
                )
            except StorageError:
                pass

            raise

        # Delete old file only after DB has successfully changed.
        # Legacy paths should not block replacement.
        if old_path and old_path != new_path:
            try:
                self._validate_stored_path(old_path)

                await self.storage_service.delete(
                    bucket=bucket,
                    path=old_path,
                )
            except StorageError:
                pass
            except StorageValidationError:
                # Old/legacy path may use an older structure.
                pass

        return signed_url, normalized_content_type

    async def get_farm_file_url(
        self,
        user_id: int,
        farm_public_id: UUID,
    ) -> tuple[str, str | None]:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        if not farm.farm_file_path:
            raise NotFoundError(
                "Farm does not have a file."
            )

        self._validate_stored_path(
            farm.farm_file_path
        )

        url, _expires = await self.storage_service.create_signed_url(
            bucket=settings.storage_bucket,
            path=farm.farm_file_path,
        )

        return url, farm.farm_file_content_type

    async def download_farm_file(
        self,
        user_id: int,
        farm_public_id: UUID,
    ) -> tuple[bytes, str]:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        if not farm.farm_file_path:
            raise NotFoundError(
                "Farm does not have a file."
            )

        self._validate_stored_path(
            farm.farm_file_path
        )

        file_bytes = await self.storage_service.download(
            bucket=settings.storage_bucket,
            path=farm.farm_file_path,
        )

        return (
            file_bytes,
            farm.farm_file_content_type
            or "application/octet-stream",
        )

    async def delete_farm_file(
        self,
        user_id: int,
        farm_public_id: UUID,
    ) -> None:
        farm = await self.get_farm(
            user_id=user_id,
            farm_public_id=farm_public_id,
        )

        if not farm.farm_file_path:
            raise NotFoundError(
                "Farm does not have a file."
            )

        old_path = farm.farm_file_path

        await self.repository.clear_file(farm.id)

        try:
            self._validate_stored_path(old_path)

            await self.storage_service.delete(
                bucket=settings.storage_bucket,
                path=old_path,
            )
        except StorageError:
            pass
        except StorageValidationError:
            pass

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------

    async def build_farm_response_data(
        self,
        farm: Farm,
    ) -> dict:
        """
        Converts DB farm data into API response data.

        farm_file_path remains internal.
        farm_file_url is generated fresh.
        """

        data = {
            "public_id": str(farm.public_id),
            "farm_name": farm.farm_name,
            "description": farm.description,
            "address_line_1": farm.address_line_1,
            "address_line_2": farm.address_line_2,
            "landmark": farm.landmark,
            "village": farm.village,
            "city": farm.city,
            "district": farm.district,
            "state": farm.state,
            "postal_code": farm.postal_code,
            "country": farm.country,
            "latitude": farm.latitude,
            "longitude": farm.longitude,
            "is_active": farm.is_active,
            "farm_file_url": None,
            "farm_file_content_type": farm.farm_file_content_type,
            "created_at": farm.created_at,
            "updated_at": farm.updated_at,
        }

        if farm.farm_file_path:
            try:
                self._validate_stored_path(
                    farm.farm_file_path
                )

                url, _expires = (
                    await self.storage_service.create_signed_url(
                        bucket=settings.storage_bucket,
                        path=farm.farm_file_path,
                    )
                )

                data["farm_file_url"] = url

            except StorageError:
                # Do not expose internal storage paths.
                data["farm_file_url"] = None

        return data