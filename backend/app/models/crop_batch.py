from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class CropBatch(Base):

    __tablename__ = "crop_batches"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    farm_crop_id: Mapped[int] = mapped_column(Integer, ForeignKey("farm_crops.id", ondelete="CASCADE"), nullable=False, index=True)

    batch_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)

    harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    available_quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    unit: Mapped[str] = mapped_column(String(30), nullable=False)

    quality_grade: Mapped[str | None] = mapped_column(String(50), nullable=True)

    organic_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    farm_crop: Mapped["FarmCrop"] = relationship("FarmCrop", foreign_keys=[CropBatch.farm_crop_id])
