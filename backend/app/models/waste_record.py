from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

from app.models.farm import Farm



class WasteRecord(Base):

    __tablename__ = "waste_records"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    crop_batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("crop_batches.id", ondelete="CASCADE"), nullable=True, index=True)

    recorded_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    waste_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    unit: Mapped[str] = mapped_column(String(30), nullable=False)

    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    farm: Mapped["Farm"] = relationship("Farm", foreign_keys=[farm_id])
