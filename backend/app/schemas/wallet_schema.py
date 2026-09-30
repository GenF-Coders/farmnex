from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# Read-only: the wallet is written only by the server (bid accept, Pay (demo), delivery, expiry).


class WalletEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID
    entry_type: str
    amount: Decimal
    currency: str
    order_id: UUID  # the order's public id
    bid_id: UUID | None = None  # the bid's public id
    payment_id: UUID | None = None  # the payment's public id
    created_at: datetime | None = None


class WalletResponse(BaseModel):
    """Demo wallet (no real money). Amounts are in INR."""

    held_from_me: Decimal  # money I paid that is still held until delivery
    held_for_me: Decimal  # money held on my sales; I get it when the order is delivered
    received: Decimal  # released to me on delivery
    refunded: Decimal  # given back to me
    entries: list[WalletEntryResponse]  # my latest ledger rows (newest first, up to 50)
