from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class CropTypeCreate(BaseModel):
    name: str
    scientific_name: str | None = None
    description: str | None = None
    category: str | None = None
    default_unit: str
    is_active: bool


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class CropTypeUpdate(BaseModel):
    name: str | None = None
    scientific_name: str | None = None
    description: str | None = None
    category: str | None = None
    default_unit: str | None = None
    is_active: bool | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class CropTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    name: str | None = None
    scientific_name: str | None = None
    description: str | None = None
    category: str | None = None
    default_unit: str | None = None
    is_active: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
