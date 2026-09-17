from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class PaymentCreate(BaseModel):
    order_id: int
    payer_id: int
    provider: str
    provider_payment_id: str | None = None
    amount: Decimal
    currency: str
    status: str
    payment_method: str | None = None
    paid_at: datetime | None = None
    failure_reason: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class PaymentUpdate(BaseModel):
    order_id: int | None = None
    payer_id: int | None = None
    provider: str | None = None
    provider_payment_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: str | None = None
    payment_method: str | None = None
    paid_at: datetime | None = None
    failure_reason: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    order_id: int | None = None
    payer_id: int | None = None
    provider: str | None = None
    provider_payment_id: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    status: str | None = None
    payment_method: str | None = None
    paid_at: datetime | None = None
    failure_reason: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
