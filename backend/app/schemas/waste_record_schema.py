from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class WasteRecordCreate(BaseModel):
    farm_id: int
    crop_batch_id: int | None = None
    recorded_by_id: int
    waste_type: str
    quantity: Decimal
    unit: str
    reason: str | None = None
    recorded_at: datetime
    status: str


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class WasteRecordUpdate(BaseModel):
    farm_id: int | None = None
    crop_batch_id: int | None = None
    recorded_by_id: int | None = None
    waste_type: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    reason: str | None = None
    recorded_at: datetime | None = None
    status: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class WasteRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    farm_id: int | None = None
    crop_batch_id: int | None = None
    recorded_by_id: int | None = None
    waste_type: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    reason: str | None = None
    recorded_at: datetime | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
