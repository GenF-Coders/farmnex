from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AIPredictionCreate(BaseModel):
    user_id: int | None = None
    farm_id: int | None = None
    farm_crop_id: int | None = None
    model_name: str
    model_version: str | None = None
    prediction_type: str
    prediction: dict
    confidence: Decimal | None = None
    predicted_for: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AIPredictionUpdate(BaseModel):
    user_id: int | None = None
    farm_id: int | None = None
    farm_crop_id: int | None = None
    model_name: str | None = None
    model_version: str | None = None
    prediction_type: str | None = None
    prediction: dict | None = None
    confidence: Decimal | None = None
    predicted_for: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AIPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    user_id: int | None = None
    farm_id: int | None = None
    farm_crop_id: int | None = None
    model_name: str | None = None
    model_version: str | None = None
    prediction_type: str | None = None
    prediction: dict | None = None
    confidence: Decimal | None = None
    predicted_for: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
