from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

from app.models.order import Order
from app.models.user import User



class Delivery(Base):

    __tablename__ = "deliveries"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)

    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    delivery_agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    pickup_address_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    delivery_address_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    expected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    order: Mapped["Order"] = relationship("Order", foreign_keys=[order_id])

    seller: Mapped["User"] = relationship("User", foreign_keys=[seller_id])
