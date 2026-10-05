from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.address_repository import AddressRepository
from app.repositories.farm_repository import FarmRepository
from app.services.address_service import AddressService


def get_address_service(
    db: AsyncSession = Depends(get_db),
) -> AddressService:
    return AddressService(
        address_repository=AddressRepository(db),
        farm_repository=FarmRepository(db),
    )