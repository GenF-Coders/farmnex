from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BuyerDemandRequestCreate(BaseModel):
    buyer_id: int
    crop_type_id: int
    title: str
    description: str | None = None
    quantity: Decimal
    unit: str
    target_price: Decimal | None = None
    delivery_city: str | None = None
    delivery_state: str | None = None
    needed_by: date | None = None
    status: str


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BuyerDemandRequestUpdate(BaseModel):
    buyer_id: int | None = None
    crop_type_id: int | None = None
    title: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    target_price: Decimal | None = None
    delivery_city: str | None = None
    delivery_state: str | None = None
    needed_by: date | None = None
    status: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BuyerDemandRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    buyer_id: int | None = None
    crop_type_id: int | None = None
    title: str | None = None
    description: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    target_price: Decimal | None = None
    delivery_city: str | None = None
    delivery_state: str | None = None
    needed_by: date | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
