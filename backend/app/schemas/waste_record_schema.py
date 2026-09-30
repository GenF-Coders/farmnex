from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import AliasPath, BaseModel, ConfigDict, Field


class WasteRecordCreate(BaseModel):
    """What the app may send. Who recorded it and the status are set by the server."""

    farm_id: UUID
    crop_batch_id: UUID | None = None
    waste_type: str = Field(min_length=1, max_length=80)
    quantity: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=30)
    reason: str | None = None
    recorded_at: datetime | None = None  # the server uses "now" when it is left out


class WasteRecordUpdate(BaseModel):
    """Only descriptive fields can change. The farm and the batch cannot be moved."""

    waste_type: str | None = Field(default=None, min_length=1, max_length=80)
    quantity: Decimal | None = Field(default=None, gt=0)
    unit: str | None = Field(default=None, min_length=1, max_length=30)
    reason: str | None = None
    recorded_at: datetime | None = None


class WasteRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    farm_id: UUID = Field(validation_alias=AliasPath("farm", "public_id"))
    # The repository puts the batch public id here (the model has no relationship to read it from).
    crop_batch_id: UUID | None = Field(default=None, validation_alias="crop_batch_public_id")
    waste_type: str
    quantity: Decimal
    unit: str
    reason: str | None = None
    recorded_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime
