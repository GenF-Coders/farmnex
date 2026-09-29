from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class CropBatchCreate(BaseModel):
    farm_crop_id: int
    batch_code: str
    harvest_date: date | None = None
    quantity: Decimal
    available_quantity: Decimal
    unit: str
    quality_grade: str | None = None
    organic_certified: bool
    status: str
    notes: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class CropBatchUpdate(BaseModel):
    farm_crop_id: int | None = None
    batch_code: str | None = None
    harvest_date: date | None = None
    quantity: Decimal | None = None
    available_quantity: Decimal | None = None
    unit: str | None = None
    quality_grade: str | None = None
    organic_certified: bool | None = None
    status: str | None = None
    notes: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class CropBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    farm_crop_id: int | None = None
    batch_code: str | None = None
    harvest_date: date | None = None
    quantity: Decimal | None = None
    available_quantity: Decimal | None = None
    unit: str | None = None
    quality_grade: str | None = None
    organic_certified: bool | None = None
    status: str | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
