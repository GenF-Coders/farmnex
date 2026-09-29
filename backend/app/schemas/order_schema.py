from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderCreate(BaseModel):
    buyer_id: int
    order_number: str
    status: str
    currency: str
    subtotal: Decimal
    delivery_fee: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    delivery_address_snapshot: dict | None = None
    placed_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderUpdate(BaseModel):
    buyer_id: int | None = None
    order_number: str | None = None
    status: str | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    delivery_fee: Decimal | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    total_amount: Decimal | None = None
    delivery_address_snapshot: dict | None = None
    placed_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    buyer_id: int | None = None
    order_number: str | None = None
    status: str | None = None
    currency: str | None = None
    subtotal: Decimal | None = None
    delivery_fee: Decimal | None = None
    tax_amount: Decimal | None = None
    discount_amount: Decimal | None = None
    total_amount: Decimal | None = None
    delivery_address_snapshot: dict | None = None
    placed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
