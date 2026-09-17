from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class DeliveryTrackingEvent(Base):

    __tablename__ = "delivery_tracking_events"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    delivery_id: Mapped[int] = mapped_column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)

    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10,7), nullable=True)

    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10,7), nullable=True)

    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    delivery: Mapped["Delivery"] = relationship("Delivery", foreign_keys=[DeliveryTrackingEvent.delivery_id])
