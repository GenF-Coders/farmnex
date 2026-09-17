from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

from app.models.crop_type import CropType
from app.models.farm import Farm
from app.models.user import User



class FarmCrop(Base):

    __tablename__ = "farm_crops"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    farmer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    crop_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("crop_types.id", ondelete="CASCADE"), nullable=False, index=True)

    variety: Mapped[str | None] = mapped_column(String(150), nullable=True)

    sowing_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    expected_harvest_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    area_value: Mapped[Decimal | None] = mapped_column(Numeric(14,3), nullable=True)

    area_unit: Mapped[str | None] = mapped_column(String(30), nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    farmer: Mapped["User"] = relationship("User", foreign_keys=[farmer_id])

    farm: Mapped["Farm"] = relationship("Farm", foreign_keys=[farm_id])

    crop_type: Mapped["CropType"] = relationship("CropType", foreign_keys=[crop_type_id])
