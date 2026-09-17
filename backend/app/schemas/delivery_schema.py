from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryCreate(BaseModel):
    order_id: int
    seller_id: int
    farm_id: int
    delivery_agent_id: int | None = None
    tracking_number: str | None = None
    status: str
    pickup_address_snapshot: dict | None = None
    delivery_address_snapshot: dict | None = None
    expected_at: datetime | None = None
    delivered_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryUpdate(BaseModel):
    order_id: int | None = None
    seller_id: int | None = None
    farm_id: int | None = None
    delivery_agent_id: int | None = None
    tracking_number: str | None = None
    status: str | None = None
    pickup_address_snapshot: dict | None = None
    delivery_address_snapshot: dict | None = None
    expected_at: datetime | None = None
    delivered_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    order_id: int | None = None
    seller_id: int | None = None
    farm_id: int | None = None
    delivery_agent_id: int | None = None
    tracking_number: str | None = None
    status: str | None = None
    pickup_address_snapshot: dict | None = None
    delivery_address_snapshot: dict | None = None
    expected_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
