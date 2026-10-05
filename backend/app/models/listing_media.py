"""Photos/videos a farmer adds to a listed lot, and the admin's "Verified by FarmNex" decision.

New tables only (prefix `lv_`); see docs/superpowers/specs/2026-10-05-listing-media-design.md.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base
from app.models.product_listing import ProductListing


class ListingMedia(Base):
    __tablename__ = "lv_listing_media"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)
    listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_listings.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # PHOTO or VIDEO
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    listing: Mapped["ProductListing"] = relationship("ProductListing", foreign_keys=[listing_id])


class ListingVerification(Base):
    __tablename__ = "lv_listing_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    listing_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("product_listings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="PENDING")  # PENDING / VERIFIED / REJECTED
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    listing: Mapped["ProductListing"] = relationship("ProductListing", foreign_keys=[listing_id])
