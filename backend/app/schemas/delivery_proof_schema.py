from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryProofCreate(BaseModel):
    delivery_id: int
    uploaded_by_id: int
    storage_path: str
    content_type: str
    proof_type: str
    captured_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryProofUpdate(BaseModel):
    delivery_id: int | None = None
    uploaded_by_id: int | None = None
    storage_path: str | None = None
    content_type: str | None = None
    proof_type: str | None = None
    captured_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class DeliveryProofResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    delivery_id: int | None = None
    uploaded_by_id: int | None = None
    storage_path: str | None = None
    content_type: str | None = None
    proof_type: str | None = None
    captured_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
