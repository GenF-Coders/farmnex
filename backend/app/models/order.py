from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class Order(Base):

    __tablename__ = "orders"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    buyer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    order_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR", server_default="INR")

    subtotal: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False)

    delivery_fee: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False, default=0, server_default="0")

    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False, default=0, server_default="0")

    discount_amount: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False, default=0, server_default="0")

    total_amount: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False)

    delivery_address_snapshot: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    placed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    buyer: Mapped["User"] = relationship("User", foreign_keys=[buyer_id])
