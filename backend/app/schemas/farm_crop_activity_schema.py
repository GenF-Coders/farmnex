from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class FarmCropActivityCreate(BaseModel):
    farm_crop_id: int
    activity_type: str
    activity_date: datetime
    description: str | None = None
    input_name: str | None = None
    input_quantity: Decimal | None = None
    input_unit: str | None = None
    cost: Decimal | None = None
    notes: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class FarmCropActivityUpdate(BaseModel):
    farm_crop_id: int | None = None
    activity_type: str | None = None
    activity_date: datetime | None = None
    description: str | None = None
    input_name: str | None = None
    input_quantity: Decimal | None = None
    input_unit: str | None = None
    cost: Decimal | None = None
    notes: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class FarmCropActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    farm_crop_id: int | None = None
    activity_type: str | None = None
    activity_date: datetime | None = None
    description: str | None = None
    input_name: str | None = None
    input_quantity: Decimal | None = None
    input_unit: str | None = None
    cost: Decimal | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
