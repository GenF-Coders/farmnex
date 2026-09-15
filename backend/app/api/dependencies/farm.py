from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.address_repository import AddressRepository
from app.repositories.farm_repository import FarmRepository
from app.services.farm_service import FarmService


def get_farm_service(
    db: AsyncSession = Depends(get_db),
) -> FarmService:
    return FarmService(
        farm_repository=FarmRepository(db),
        address_repository=AddressRepository(db),
    )