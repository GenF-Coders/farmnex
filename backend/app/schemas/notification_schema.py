from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    notification_type: str
    data: dict | None = None
    is_read: bool
    read_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class NotificationUpdate(BaseModel):
    user_id: int | None = None
    title: str | None = None
    message: str | None = None
    notification_type: str | None = None
    data: dict | None = None
    is_read: bool | None = None
    read_at: datetime | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    user_id: int | None = None
    title: str | None = None
    message: str | None = None
    notification_type: str | None = None
    data: dict | None = None
    is_read: bool | None = None
    read_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
