from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

from app.models.product_listing import ProductListing



class ProductImage(Base):

    __tablename__ = "product_images"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("product_listings.id", ondelete="CASCADE"), nullable=False, index=True)

    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    listing: Mapped["ProductListing"] = relationship("ProductListing", foreign_keys=[listing_id])
