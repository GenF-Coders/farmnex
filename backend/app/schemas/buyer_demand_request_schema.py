from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AliasPath, BaseModel, ConfigDict, Field


class BuyerDemandRequestCreate(BaseModel):
    """What the app may send. The buyer and the status are set by the server."""

    crop_type_id: UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    quantity: Decimal = Field(gt=0, lt=10**11)
    unit: str = Field(min_length=1, max_length=30)
    target_price: Decimal | None = Field(default=None, ge=0, lt=10**12)
    delivery_city: str | None = Field(default=None, max_length=150)
    delivery_state: str | None = Field(default=None, max_length=150)
    needed_by: date | None = None


class BuyerDemandRequestUpdate(BaseModel):
    """The crop type cannot change. The owner may close the request (or re-open it)."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    quantity: Decimal | None = Field(default=None, gt=0, lt=10**11)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    target_price: Decimal | None = Field(default=None, ge=0, lt=10**12)
    delivery_city: str | None = Field(default=None, max_length=150)
    delivery_state: str | None = Field(default=None, max_length=150)
    needed_by: date | None = None
    status: Literal["ACTIVE", "CLOSED"] | None = None


class BuyerDemandRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    buyer_id: UUID = Field(validation_alias=AliasPath("buyer", "public_id"))
    crop_type_id: UUID = Field(validation_alias=AliasPath("crop_type", "public_id"))
    title: str
    description: str | None = None
    quantity: Decimal
    unit: str
    target_price: Decimal | None = None
    delivery_city: str | None = None
    delivery_state: str | None = None
    needed_by: date | None = None
    status: str
    created_at: datetime
    updated_at: datetime
