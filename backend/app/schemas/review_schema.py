from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ReviewCreate(BaseModel):
    reviewer_id: int
    order_id: int
    listing_id: int | None = None
    reviewee_id: int
    rating: int
    title: str | None = None
    comment: str | None = None
    status: str


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ReviewUpdate(BaseModel):
    reviewer_id: int | None = None
    order_id: int | None = None
    listing_id: int | None = None
    reviewee_id: int | None = None
    rating: int | None = None
    title: str | None = None
    comment: str | None = None
    status: str | None = None


from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    public_id: UUID | None = None
    reviewer_id: int | None = None
    order_id: int | None = None
    listing_id: int | None = None
    reviewee_id: int | None = None
    rating: int | None = None
    title: str | None = None
    comment: str | None = None
    status: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
