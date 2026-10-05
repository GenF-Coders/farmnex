"""Lot photos/videos and the admin's "Verified by FarmNex" decision.

Rules (docs/superpowers/specs/2026-10-05-listing-media-design.md):
- only the listing's seller adds or deletes media; anyone who can see the listing can view it;
- 6 photos + 2 videos per lot, each file at most the storage upload limit (10 MB), with a real
  JPG/PNG/WebP or MP4/MOV signature;
- any media change puts the lot back to PENDING (the badge comes off);
- only ADMIN / SUPER_ADMIN decide, and a rejection needs a reason.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError, ValidationError
from app.models.listing_media import ListingMedia, ListingVerification
from app.models.product_listing import ProductListing
from app.models.user import User
from app.repositories.listing_media_repository import ListingMediaRepository
from app.services.storage_service import StorageError, StorageService, StorageValidationError

logger = logging.getLogger(__name__)

FOLDER = "listing-media"
MAX_PHOTOS = 6
MAX_VIDEOS = 2
REVIEWER_ROLES = frozenset({"ADMIN", "SUPER_ADMIN"})

PHOTO_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
VIDEO_TYPES = {"video/mp4": "mp4", "video/quicktime": "mov"}


@dataclass
class MediaItem:
    media: ListingMedia
    url: str | None  # short-lived signed link, None if storage couldn't make one


@dataclass
class MediaOverview:
    listing: ProductListing
    items: list[MediaItem]
    verification: ListingVerification | None


def _is_video(file_bytes: bytes) -> bool:
    """MP4 and MOV both carry an 'ftyp' box right after the first 4 bytes."""
    return len(file_bytes) >= 12 and file_bytes[4:8] == b"ftyp"


class ListingMediaService:
    def __init__(self, repository: ListingMediaRepository, storage: StorageService) -> None:
        self.repository = repository
        self.storage = storage

    # --- helpers --------------------------------------------------------------------

    async def _owned_listing(self, listing_public_id: UUID, user: User) -> ProductListing:
        listing = await self.repository.get_listing_owned_by_user(listing_public_id, user.id)
        if listing is None:
            raise NotFoundError("ProductListing not found.")
        return listing

    async def _signed(self, media: ListingMedia) -> str | None:
        try:
            return await self.storage.create_signed_url(bucket=settings.storage_bucket, path=media.storage_path)
        except StorageError:
            logger.exception("Could not sign listing media %s", media.public_id)
            return None

    async def _overview(self, listing: ProductListing) -> MediaOverview:
        media = await self.repository.list_media(listing.id)
        items = [MediaItem(media=m, url=await self._signed(m)) for m in media]
        return MediaOverview(listing=listing, items=items, verification=await self.repository.get_verification(listing.id))

    def _check_file(self, file_bytes: bytes, content_type: str) -> tuple[str, str, str]:
        """(kind, normalised content type, file extension), or ValidationError."""
        try:
            normalized = self.storage.validate_file(
                file_bytes=file_bytes, content_type=content_type, verify_signature=True
            )
        except StorageValidationError as exc:
            raise ValidationError(str(exc)) from exc
        if normalized in PHOTO_TYPES:
            return "PHOTO", normalized, PHOTO_TYPES[normalized]
        if normalized in VIDEO_TYPES:
            if not _is_video(file_bytes):
                raise ValidationError("Uploaded file content does not match its content type.")
            return "VIDEO", normalized, VIDEO_TYPES[normalized]
        raise ValidationError("Only photos (JPG, PNG, WebP) and videos (MP4, MOV) can be added.")

    # --- farmer + buyer ---------------------------------------------------------------

    async def list(self, listing_public_id: UUID, user: User) -> MediaOverview:
        listing = await self.repository.get_listing_visible_to(listing_public_id, user.id)
        if listing is None and (user.role is not None and user.role.name.upper() in REVIEWER_ROLES):
            listing = await self.repository.get_listing(listing_public_id)  # admins review any lot
        if listing is None:
            raise NotFoundError("ProductListing not found.")
        return await self._overview(listing)

    async def add(self, listing_public_id: UUID, user: User, *, file_bytes: bytes, content_type: str) -> MediaOverview:
        listing = await self._owned_listing(listing_public_id, user)
        if listing.status == "CLOSED":
            raise ConflictError("This listing is closed; photos can no longer be added.")
        kind, normalized, extension = self._check_file(file_bytes, content_type)
        limit = MAX_PHOTOS if kind == "PHOTO" else MAX_VIDEOS
        if await self.repository.count_media(listing.id, kind) >= limit:
            raise ConflictError(f"A lot can have at most {MAX_PHOTOS} photos and {MAX_VIDEOS} videos.")

        path = f"{FOLDER}/{uuid4()}.{extension}"
        try:
            # The signature was checked above (videos by _is_video); the storage service knows only images.
            await self.storage.upload(
                bucket=settings.storage_bucket, path=path, file_bytes=file_bytes,
                content_type=normalized, verify_signature=False,
            )
        except StorageValidationError as exc:
            raise ValidationError(str(exc)) from exc
        except StorageError as exc:
            logger.exception("Listing media upload failed")
            raise ServiceUnavailableError("File storage is temporarily unavailable.") from exc

        await self.repository.add_media(
            listing_id=listing.id, uploaded_by_id=user.id, kind=kind, storage_path=path,
            content_type=normalized, size_bytes=len(file_bytes),
        )
        await self.repository.set_verification(listing.id, status="PENDING")  # badge off until re-checked
        return await self._overview(listing)

    async def delete(self, listing_public_id: UUID, media_public_id: UUID, user: User) -> MediaOverview:
        listing = await self._owned_listing(listing_public_id, user)
        media = await self.repository.get_media(listing.id, media_public_id)
        if media is None:
            raise NotFoundError("Media not found.")
        path = media.storage_path
        await self.repository.delete_media(media)
        if await self.repository.list_media(listing.id):
            await self.repository.set_verification(listing.id, status="PENDING")
        else:
            await self.repository.clear_verification(listing.id)  # nothing left to review
        try:
            await self.storage.delete(bucket=settings.storage_bucket, path=path)
        except StorageError:
            logger.exception("Could not delete listing media file %s", media_public_id)  # the row is gone anyway
        return await self._overview(listing)

    async def badges(self, listing_ids: list[int]) -> tuple[dict[int, str], dict[int, int]]:
        """(verification status, media count) for several listings at once — for listing responses."""
        return await self.repository.statuses(listing_ids), await self.repository.media_counts(listing_ids)

    # --- admin ------------------------------------------------------------------------

    async def queue(self, status: str, *, offset: int, limit: int) -> list[tuple[ListingVerification, ProductListing, int]]:
        if status not in ("PENDING", "VERIFIED", "REJECTED"):
            raise ValidationError("status must be PENDING, VERIFIED or REJECTED.")
        if offset < 0 or not 1 <= limit <= 100:
            raise ValidationError("Limit must be between 1 and 100.")
        rows = await self.repository.list_by_status(status, offset=offset, limit=limit)
        counts = await self.repository.media_counts([listing.id for _, listing in rows])
        return [(verification, listing, counts.get(listing.id, 0)) for verification, listing in rows]

    async def decide(self, listing_public_id: UUID, reviewer: User, *, decision: str, reason: str | None) -> MediaOverview:
        listing = await self.repository.get_listing(listing_public_id)
        if listing is None:
            raise NotFoundError("ProductListing not found.")
        if not await self.repository.list_media(listing.id):
            raise ConflictError("This lot has no photos or videos to verify.")
        reason = (reason or "").strip() or None
        if decision == "REJECTED" and reason is None:
            raise ValidationError("Please give the farmer a reason for the rejection.")
        await self.repository.set_verification(
            listing.id, status=decision, reason=reason if decision == "REJECTED" else None,
            reviewed_by_id=reviewer.id, reviewed_at=datetime.now(timezone.utc),
        )
        return await self._overview(listing)
