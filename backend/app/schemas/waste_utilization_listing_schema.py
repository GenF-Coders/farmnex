from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AliasPath, BaseModel, ConfigDict, Field


class WasteUtilizationListingCreate(BaseModel):
    """What the app may send. The seller and the status are set by the server."""

    waste_record_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    utilization_type: str = Field(min_length=1, max_length=50)
    quantity: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=30)
    price: Decimal = Field(ge=0)


class WasteUtilizationListingUpdate(BaseModel):
    """The waste record it belongs to cannot change. The owner may close or re-open the listing."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    utilization_type: str | None = Field(default=None, min_length=1, max_length=50)
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    price: Decimal | None = Field(default=None, ge=0)
    status: Literal["ACTIVE", "CLOSED"] | None = None


class WasteUtilizationListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    waste_record_id: UUID = Field(validation_alias=AliasPath("waste_record", "public_id"))
    seller_id: UUID = Field(validation_alias=AliasPath("seller", "public_id"))
    title: str
    description: str | None = None
    utilization_type: str
    quantity: Decimal
    unit: str
    price: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
