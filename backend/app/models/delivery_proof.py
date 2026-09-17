from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class DeliveryProof(Base):

    __tablename__ = "delivery_proofs"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    delivery_id: Mapped[int] = mapped_column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True)

    uploaded_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)

    content_type: Mapped[str] = mapped_column(String(100), nullable=False)

    proof_type: Mapped[str] = mapped_column(String(50), nullable=False)

    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    delivery: Mapped["Delivery"] = relationship("Delivery", foreign_keys=[DeliveryProof.delivery_id])

    uploaded_by: Mapped["User"] = relationship("User", foreign_keys=[DeliveryProof.uploaded_by_id])
