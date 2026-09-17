from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class WasteUtilizationListing(Base):

    __tablename__ = "waste_utilization_listings"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    waste_record_id: Mapped[int] = mapped_column(Integer, ForeignKey("waste_records.id", ondelete="CASCADE"), nullable=False, index=True)

    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    utilization_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    unit: Mapped[str] = mapped_column(String(30), nullable=False)

    price: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    waste_record: Mapped["WasteRecord"] = relationship("WasteRecord", foreign_keys=[WasteUtilizationListing.waste_record_id])

    seller: Mapped["User"] = relationship("User", foreign_keys=[WasteUtilizationListing.seller_id])
