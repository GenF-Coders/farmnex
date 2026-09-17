from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BidCreate(BaseModel):
    bid_event_id: int
    bidder_id: int
    amount: Decimal
    quantity: Decimal | None = None
    status: str
    placed_at: datetime


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BidUpdate(BaseModel):
    bid_event_id: int | None = None
    bidder_id: int | None = None
    amount: Decimal | None = None
    quantity: Decimal | None = None
    status: str | None = None
    placed_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BidResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    bid_event_id: int | None = None
    bidder_id: int | None = None
    amount: Decimal | None = None
    quantity: Decimal | None = None
    status: str | None = None
    placed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
