from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.database import get_db
from app.repositories.farm_repository import FarmRepository
from app.services.farm_service import FarmService
from app.services.storage_service import storage_service


def get_farm_service(
    db: AsyncSession = Depends(get_db),
) -> FarmService:
    return FarmService(
        repository=FarmRepository(db),
        storage_service=storage_service,
    )