from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Date, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class BuyerDemandRequest(Base):

    __tablename__ = "buyer_demand_requests"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    crop_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("crop_types.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    unit: Mapped[str] = mapped_column(String(30), nullable=False)

    target_price: Mapped[Decimal | None] = mapped_column(Numeric(14,2), nullable=True)

    delivery_city: Mapped[str | None] = mapped_column(String(150), nullable=True)

    delivery_state: Mapped[str | None] = mapped_column(String(150), nullable=True)

    needed_by: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    buyer: Mapped["User"] = relationship("User", foreign_keys=[BuyerDemandRequest.buyer_id])

    crop_type: Mapped["CropType"] = relationship("CropType", foreign_keys=[BuyerDemandRequest.crop_type_id])
