from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles
from app.api.v2.endpoints.listing_media_controller import get_listing_media_service
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.product_listing import ProductListing
from app.models.user import User
from app.modules import crop_rescue_host
from app.repositories.product_listing_repository import ProductListingRepository
from app.schemas.product_listing_schema import ProductListingCreate, ProductListingResponse, ProductListingUpdate
from app.services.listing_media_service import ListingMediaService
from app.services.product_listing_service import ProductListingService

router = APIRouter(prefix="/product-listings", tags=["ProductListing"])


def get_product_listing_service(db: AsyncSession = Depends(get_db)) -> ProductListingService:
    return ProductListingService(ProductListingRepository(db))


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


async def _with_badges(entities: list[ProductListing], media: ListingMediaService) -> list[ProductListingResponse]:
    """Listing responses plus the "Verified by FarmNex" status and photo count (one query each)."""
    statuses, counts = await media.badges([entity.id for entity in entities])
    return [
        ProductListingResponse.model_validate(entity).model_copy(
            update={"verification_status": statuses.get(entity.id, "NONE"), "media_count": counts.get(entity.id, 0)}
        )
        for entity in entities
    ]


@router.post("", response_model=ProductListingResponse, status_code=status.HTTP_201_CREATED)
async def create(
    payload: ProductListingCreate,
    current_user: User = Depends(require_roles("FARMER", "VENDOR")),
    service: ProductListingService = Depends(get_product_listing_service),
) -> ProductListingResponse:
    try:
        entity = await service.create(payload.model_dump(exclude_unset=True), current_user)
        # Every normal lot gets a Crop Rescue spoilage timer; this never fails the listing.
        rescue_lot_id, rescue_note = await crop_rescue_host.start_timer_for_listing(
            entity, current_user, await service.crop_type_of(entity)
        )
        response = ProductListingResponse.model_validate(entity)
        return response.model_copy(update={"rescue_lot_id": rescue_lot_id, "rescue_note": rescue_note})
    except AppException as exc:
        _raise_http(exc)


@router.get("", response_model=list[ProductListingResponse])
async def list_all(
    mine: bool = Query(False, description="Only my own listings (any status)."),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ProductListingService = Depends(get_product_listing_service),
    media: ListingMediaService = Depends(get_listing_media_service),
) -> list[ProductListingResponse]:
    try:
        entities, _ = await service.list(current_user=current_user, only_mine=mine, offset=offset, limit=limit)
        return await _with_badges(entities, media)
    except AppException as exc:
        _raise_http(exc)


@router.get("/{public_id}", response_model=ProductListingResponse)
async def get_one(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ProductListingService = Depends(get_product_listing_service),
    media: ListingMediaService = Depends(get_listing_media_service),
) -> ProductListingResponse:
    try:
        return (await _with_badges([await service.get(public_id, current_user)], media))[0]
    except AppException as exc:
        _raise_http(exc)


@router.patch("/{public_id}", response_model=ProductListingResponse)
async def update(
    public_id: UUID,
    payload: ProductListingUpdate,
    current_user: User = Depends(get_current_user),
    service: ProductListingService = Depends(get_product_listing_service),
) -> ProductListingResponse:
    try:
        entity = await service.update(public_id, payload.model_dump(exclude_unset=True), current_user)
        return ProductListingResponse.model_validate(entity)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/{public_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    public_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ProductListingService = Depends(get_product_listing_service),
) -> None:
    """Closes the listing (status CLOSED); it is not erased."""
    try:
        await service.delete(public_id, current_user)
    except AppException as exc:
        _raise_http(exc)
