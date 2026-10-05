"""Lot photos/videos (farmer adds, everyone who sees the listing views) and admin verification."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.repositories.listing_media_repository import ListingMediaRepository
from app.schemas.listing_media_schema import (
    ListingMediaItem,
    ListingMediaResponse,
    ListingVerificationOut,
    VerificationDecision,
    VerificationQueueItem,
)
from app.services.listing_media_service import MAX_PHOTOS, MAX_VIDEOS, ListingMediaService, MediaOverview
from app.services.storage_service import storage_service

router = APIRouter(tags=["ListingMedia"])


def get_listing_media_service(db: AsyncSession = Depends(get_db)) -> ListingMediaService:
    return ListingMediaService(ListingMediaRepository(db), storage_service)


def _raise_http(exc: AppException) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def _response(overview: MediaOverview) -> ListingMediaResponse:
    verification = overview.verification
    return ListingMediaResponse(
        listing_id=overview.listing.public_id,
        verification=ListingVerificationOut(
            status=verification.status if verification is not None else "NONE",
            reason=verification.reason if verification is not None else None,
            reviewed_at=verification.reviewed_at if verification is not None else None,
        ),
        items=[
            ListingMediaItem(
                public_id=item.media.public_id,
                kind=item.media.kind,
                content_type=item.media.content_type,
                size_bytes=item.media.size_bytes,
                url=item.url,
                created_at=item.media.created_at,
            )
            for item in overview.items
        ],
        max_photos=MAX_PHOTOS,
        max_videos=MAX_VIDEOS,
    )


@router.get("/product-listings/{listing_id}/media", response_model=ListingMediaResponse)
async def list_media(
    listing_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ListingMediaService = Depends(get_listing_media_service),
) -> ListingMediaResponse:
    try:
        return _response(await service.list(listing_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.post(
    "/product-listings/{listing_id}/media",
    response_model=ListingMediaResponse,
    status_code=status.HTTP_201_CREATED,
    description="Add one camera photo (JPG/PNG/WebP) or short video (MP4/MOV), max 10 MB, to your own lot.",
)
async def add_media(
    listing_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_roles("FARMER", "VENDOR")),
    service: ListingMediaService = Depends(get_listing_media_service),
) -> ListingMediaResponse:
    # Read at most one byte over the limit, so a huge upload is refused without holding it all.
    file_bytes = await file.read(settings.storage_max_upload_size_bytes + 1)
    try:
        overview = await service.add(
            listing_id, current_user, file_bytes=file_bytes,
            content_type=file.content_type or "application/octet-stream",
        )
        return _response(overview)
    except AppException as exc:
        _raise_http(exc)


@router.delete("/product-listings/{listing_id}/media/{media_id}", response_model=ListingMediaResponse)
async def delete_media(
    listing_id: UUID,
    media_id: UUID,
    current_user: User = Depends(require_roles("FARMER", "VENDOR")),
    service: ListingMediaService = Depends(get_listing_media_service),
) -> ListingMediaResponse:
    try:
        return _response(await service.delete(listing_id, media_id, current_user))
    except AppException as exc:
        _raise_http(exc)


@router.get("/admin/listing-verifications", response_model=list[VerificationQueueItem])
async def verification_queue(
    status_filter: str = Query("PENDING", alias="status", description="PENDING, VERIFIED or REJECTED"),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    _: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
    service: ListingMediaService = Depends(get_listing_media_service),
) -> list[VerificationQueueItem]:
    try:
        rows = await service.queue(status_filter.upper(), offset=offset, limit=limit)
    except AppException as exc:
        _raise_http(exc)
    return [
        VerificationQueueItem(
            listing_id=listing.public_id, title=listing.title, listing_type=listing.listing_type,
            price=listing.price, unit=listing.unit, status=verification.status, reason=verification.reason,
            media_count=count, updated_at=verification.updated_at,
        )
        for verification, listing, count in rows
    ]


@router.post("/admin/listing-verifications/{listing_id}", response_model=ListingMediaResponse)
async def decide_verification(
    listing_id: UUID,
    payload: VerificationDecision,
    current_user: User = Depends(require_roles("ADMIN", "SUPER_ADMIN")),
    service: ListingMediaService = Depends(get_listing_media_service),
) -> ListingMediaResponse:
    try:
        overview = await service.decide(listing_id, current_user, decision=payload.decision, reason=payload.reason)
        return _response(overview)
    except AppException as exc:
        _raise_http(exc)
