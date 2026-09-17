from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class WasteUtilizationListingCreate(BaseModel):
    waste_record_id: int
    seller_id: int
    title: str
    description: str | None = None
    utilization_type: str
    quantity: Decimal
    unit: str
    price: Decimal
    status: str


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class WasteUtilizationListingUpdate(BaseModel):
    waste_record_id: int | None = None
    seller_id: int | None = None
    title: str | None = None
    description: str | None = None
    utilization_type: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    price: Decimal | None = None
    status: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class WasteUtilizationListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    waste_record_id: int | None = None
    seller_id: int | None = None
    title: str | None = None
    description: str | None = None
    utilization_type: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    price: Decimal | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
