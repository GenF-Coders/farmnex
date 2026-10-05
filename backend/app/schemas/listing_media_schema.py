from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ListingMediaItem(BaseModel):
    """One photo or video. `url` is a short-lived signed link (null if storage is briefly unavailable)."""

    public_id: UUID
    kind: Literal["PHOTO", "VIDEO"]
    content_type: str
    size_bytes: int
    url: str | None
    created_at: datetime


class ListingVerificationOut(BaseModel):
    """NONE = no photos yet; PENDING = waiting for FarmNex; VERIFIED = ✅ badge; REJECTED = see `reason`."""

    status: Literal["NONE", "PENDING", "VERIFIED", "REJECTED"]
    reason: str | None = None
    reviewed_at: datetime | None = None


class ListingMediaResponse(BaseModel):
    listing_id: UUID
    verification: ListingVerificationOut
    items: list[ListingMediaItem]
    max_photos: int
    max_videos: int


class VerificationDecision(BaseModel):
    """What an admin may send. Who decided and when are set by the server."""

    decision: Literal["VERIFIED", "REJECTED"]
    reason: str | None = Field(default=None, max_length=500)


class VerificationQueueItem(BaseModel):
    listing_id: UUID
    title: str
    listing_type: str
    price: Decimal
    unit: str
    status: Literal["PENDING", "VERIFIED", "REJECTED"]
    reason: str | None = None
    media_count: int
    updated_at: datetime
