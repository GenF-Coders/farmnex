from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AuditLogCreate(BaseModel):
    actor_id: int | None = None
    action: str
    entity_type: str
    entity_id: int | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    before_data: dict | None = None
    after_data: dict | None = None
    created_at_override: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AuditLogUpdate(BaseModel):
    actor_id: int | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    before_data: dict | None = None
    after_data: dict | None = None
    created_at_override: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    actor_id: int | None = None
    action: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    request_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    before_data: dict | None = None
    after_data: dict | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
