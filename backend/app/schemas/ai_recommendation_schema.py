from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AIRecommendationCreate(BaseModel):
    user_id: int
    farm_id: int | None = None
    farm_crop_id: int | None = None
    prediction_id: int | None = None
    recommendation_type: str
    title: str
    description: str
    priority: str
    status: str
    metadata_json: dict | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AIRecommendationUpdate(BaseModel):
    user_id: int | None = None
    farm_id: int | None = None
    farm_crop_id: int | None = None
    prediction_id: int | None = None
    recommendation_type: str | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    metadata_json: dict | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AIRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    user_id: int | None = None
    farm_id: int | None = None
    farm_crop_id: int | None = None
    prediction_id: int | None = None
    recommendation_type: str | None = None
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None
    metadata_json: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
