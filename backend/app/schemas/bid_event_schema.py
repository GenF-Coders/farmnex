from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BidEventCreate(BaseModel):
    listing_id: int
    created_by_id: int
    starts_at: datetime
    ends_at: datetime
    starting_price: Decimal
    minimum_increment: Decimal
    status: str
    winner_bid_id: int | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BidEventUpdate(BaseModel):
    listing_id: int | None = None
    created_by_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    starting_price: Decimal | None = None
    minimum_increment: Decimal | None = None
    status: str | None = None
    winner_bid_id: int | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class BidEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    listing_id: int | None = None
    created_by_id: int | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    starting_price: Decimal | None = None
    minimum_increment: Decimal | None = None
    status: str | None = None
    winner_bid_id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
