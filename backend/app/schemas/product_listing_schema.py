from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ProductListingCreate(BaseModel):
    seller_id: int
    farm_id: int
    crop_batch_id: int
    title: str
    description: str | None = None
    listing_type: str
    price: Decimal
    currency: str
    quantity: Decimal
    available_quantity: Decimal
    unit: str
    minimum_order_quantity: Decimal | None = None
    status: str
    starts_at: datetime | None = None
    ends_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ProductListingUpdate(BaseModel):
    seller_id: int | None = None
    farm_id: int | None = None
    crop_batch_id: int | None = None
    title: str | None = None
    description: str | None = None
    listing_type: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    quantity: Decimal | None = None
    available_quantity: Decimal | None = None
    unit: str | None = None
    minimum_order_quantity: Decimal | None = None
    status: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ProductListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    seller_id: int | None = None
    farm_id: int | None = None
    crop_batch_id: int | None = None
    title: str | None = None
    description: str | None = None
    listing_type: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    quantity: Decimal | None = None
    available_quantity: Decimal | None = None
    unit: str | None = None
    minimum_order_quantity: Decimal | None = None
    status: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
