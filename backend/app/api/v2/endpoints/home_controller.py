from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.home_service import HomeService

router = APIRouter(prefix="/home", tags=["Home"])


def get_home_service(db: AsyncSession = Depends(get_db)) -> HomeService:
    return HomeService(db)


@router.get("", status_code=status.HTTP_200_OK)
async def get_home(
    latitude: float | None = Query(default=None, ge=-90, le=90),
    longitude: float | None = Query(default=None, ge=-180, le=180),
    city: str | None = Query(default=None, min_length=1, max_length=150),
    area: str | None = Query(default=None, min_length=1, max_length=150),
    radius_km: float = Query(default=25.0, gt=0, le=200),
    limit: int = Query(default=20, ge=1, le=100),
    service: HomeService = Depends(get_home_service),
) -> dict:
    try:
        return await service.get_home(
            latitude=latitude,
            longitude=longitude,
            city=city,
            area=area,
            radius_km=radius_km,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
