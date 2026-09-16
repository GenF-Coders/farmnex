from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.farm_repository import FarmRepository
from app.services.farm_service import FarmService
from app.services.storage_service import storage_service


def get_farm_repository(
    db: AsyncSession = Depends(get_db),
) -> FarmRepository:
    """
    Build the FarmRepository for the current request.
    """
    return FarmRepository(
        db=db,
    )


def get_farm_service(
    farm_repository: FarmRepository = Depends(
        get_farm_repository
    ),
) -> FarmService:
    """
    Build FarmService for the current request.

    FarmService owns:
        - farm business rules
        - farmer ownership
        - farm address data
        - farm file lifecycle

    StorageService remains the generic storage infrastructure layer.
    """
    return FarmService(
        farm_repository=farm_repository,
        storage_service=storage_service,
    )