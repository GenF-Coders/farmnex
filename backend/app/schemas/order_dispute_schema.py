from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderDisputeCreate(BaseModel):
    order_id: int
    raised_by_id: int
    against_user_id: int | None = None
    reason: str
    description: str
    status: str
    resolution: str | None = None
    resolved_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderDisputeUpdate(BaseModel):
    order_id: int | None = None
    raised_by_id: int | None = None
    against_user_id: int | None = None
    reason: str | None = None
    description: str | None = None
    status: str | None = None
    resolution: str | None = None
    resolved_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class OrderDisputeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    order_id: int | None = None
    raised_by_id: int | None = None
    against_user_id: int | None = None
    reason: str | None = None
    description: str | None = None
    status: str | None = None
    resolution: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
