from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class FarmCropCreate(BaseModel):
    farmer_id: int
    farm_id: int
    crop_type_id: int
    variety: str | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    area_value: Decimal | None = None
    area_unit: str | None = None
    status: str
    notes: str | None = None
    is_active: bool


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class FarmCropUpdate(BaseModel):
    farmer_id: int | None = None
    farm_id: int | None = None
    crop_type_id: int | None = None
    variety: str | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    area_value: Decimal | None = None
    area_unit: str | None = None
    status: str | None = None
    notes: str | None = None
    is_active: bool | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class FarmCropResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    farmer_id: int | None = None
    farm_id: int | None = None
    crop_type_id: int | None = None
    variety: str | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    area_value: Decimal | None = None
    area_unit: str | None = None
    status: str | None = None
    notes: str | None = None
    is_active: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
