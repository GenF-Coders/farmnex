from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.profile_repository import ProfileRepository
from app.services.profile_service import ProfileService
from app.services.storage_service import StorageService


def get_profile_service(
    db: AsyncSession = Depends(get_db),
) -> ProfileService:
    return ProfileService(
        profile_repository=ProfileRepository(db),
        storage_service=StorageService(),
    )