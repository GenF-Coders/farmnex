from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryTrackingEventCreate(BaseModel):
    delivery_id: int
    status: str
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    location_text: str | None = None
    notes: str | None = None
    recorded_at: datetime


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryTrackingEventUpdate(BaseModel):
    delivery_id: int | None = None
    status: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    location_text: str | None = None
    notes: str | None = None
    recorded_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryTrackingEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    delivery_id: int | None = None
    status: str | None = None
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    location_text: str | None = None
    notes: str | None = None
    recorded_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
