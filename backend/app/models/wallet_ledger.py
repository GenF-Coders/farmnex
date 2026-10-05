from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class WalletLedgerEntry(Base):
    """One line in the demo wallet (F12 / S20). Rows are only ever added, never changed.

    HOLD    - the buyer's money is held for an order (`user_public_id` = the buyer)
    RELEASE - held money goes to the farmer on delivery (`user_public_id` = the farmer)
    REFUND  - held money goes back to the buyer (`user_public_id` = the buyer)

    Money still held for an order = its HOLDs - RELEASEs - REFUNDs. `idempotency_key` is made by the
    server (e.g. "HOLD:BID:<bid id>") and is unique, so each step can happen only once.
    """

    __tablename__ = "wallet_ledger"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_wallet_ledger_amount_positive"),
        CheckConstraint("entry_type IN ('HOLD', 'RELEASE', 'REFUND')", name="ck_wallet_ledger_entry_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False, index=True, default=uuid4)

    user_public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    order_public_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)

    bid_public_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    payment_public_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR", server_default="INR")

    idempotency_key: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)

    # The client's Idempotency-Key header, kept only to trace a request (never used for uniqueness).
    request_key: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
