from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class FarmCropActivity(Base):

    __tablename__ = "farm_crop_activities"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    farm_crop_id: Mapped[int] = mapped_column(Integer, ForeignKey("farm_crops.id", ondelete="CASCADE"), nullable=False, index=True)

    activity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    activity_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    input_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    input_quantity: Mapped[Decimal | None] = mapped_column(Numeric(14,3), nullable=True)

    input_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)

    cost: Mapped[Decimal | None] = mapped_column(Numeric(14,2), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    farm_crop: Mapped["FarmCrop"] = relationship("FarmCrop", foreign_keys=[FarmCropActivity.farm_crop_id])
