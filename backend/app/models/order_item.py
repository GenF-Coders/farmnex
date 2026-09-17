from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import Integer, Numeric, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class OrderItem(Base):

    __tablename__ = "order_items"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)

    seller_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id", ondelete="CASCADE"), nullable=False, index=True)

    listing_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("product_listings.id", ondelete="CASCADE"), nullable=True, index=True)

    crop_batch_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("crop_batches.id", ondelete="CASCADE"), nullable=True, index=True)

    title_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)

    unit_price: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False)

    quantity: Mapped[Decimal] = mapped_column(Numeric(14,3), nullable=False)

    unit: Mapped[str] = mapped_column(String(30), nullable=False)

    line_total: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    order: Mapped["Order"] = relationship("Order", foreign_keys=[OrderItem.order_id])

    seller: Mapped["User"] = relationship("User", foreign_keys=[OrderItem.seller_id])

    farm: Mapped["Farm"] = relationship("Farm", foreign_keys=[OrderItem.farm_id])
