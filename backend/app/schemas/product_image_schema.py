from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ProductImageCreate(BaseModel):
    listing_id: int
    storage_path: str
    content_type: str
    sort_order: int
    is_primary: bool


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ProductImageUpdate(BaseModel):
    listing_id: int | None = None
    storage_path: str | None = None
    content_type: str | None = None
    sort_order: int | None = None
    is_primary: bool | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ProductImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    listing_id: int | None = None
    storage_path: str | None = None
    content_type: str | None = None
    sort_order: int | None = None
    is_primary: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
