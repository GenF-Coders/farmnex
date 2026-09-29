from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderItemCreate(BaseModel):
    order_id: int
    seller_id: int
    farm_id: int
    listing_id: int | None = None
    crop_batch_id: int | None = None
    title_snapshot: str
    unit_price: Decimal
    quantity: Decimal
    unit: str
    line_total: Decimal
    status: str


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderItemUpdate(BaseModel):
    order_id: int | None = None
    seller_id: int | None = None
    farm_id: int | None = None
    listing_id: int | None = None
    crop_batch_id: int | None = None
    title_snapshot: str | None = None
    unit_price: Decimal | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    line_total: Decimal | None = None
    status: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    order_id: int | None = None
    seller_id: int | None = None
    farm_id: int | None = None
    listing_id: int | None = None
    crop_batch_id: int | None = None
    title_snapshot: str | None = None
    unit_price: Decimal | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    line_total: Decimal | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
