from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base



class Bid(Base):

    __tablename__ = "bids"



    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    bid_event_id: Mapped[int] = mapped_column(Integer, ForeignKey("bid_events.id", ondelete="CASCADE"), nullable=False, index=True)

    bidder_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    amount: Mapped[Decimal] = mapped_column(Numeric(14,2), nullable=False)

    quantity: Mapped[Decimal | None] = mapped_column(Numeric(14,3), nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True, default="ACTIVE", server_default="ACTIVE")

    placed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    bid_event: Mapped["BidEvent"] = relationship("BidEvent", foreign_keys=[Bid.bid_event_id])

    bidder: Mapped["User"] = relationship("User", foreign_keys=[Bid.bidder_id])
