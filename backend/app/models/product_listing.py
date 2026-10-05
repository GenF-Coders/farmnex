from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

from app.models.crop_batch import CropBatch
from app.models.farm import Farm
from app.models.user import User



class ProductListing(Base):

    __tablename__ = "product_listings"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    crop_batch_id: Mapped[int] = mapped_column(Integer, ForeignKey("crop_batches.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    listing_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    price: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False)

    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR", server_default="INR")

    quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    available_quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    unit: Mapped[str] = mapped_column(String(30), nullable=False)

    minimum_order_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14,3), nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])

    farm: Mapped["Farm"] = relationship("Farm", foreign_keys=[farm_id])

    crop_batch: Mapped["CropBatch"] = relationship("CropBatch", foreign_keys=[crop_batch_id])
