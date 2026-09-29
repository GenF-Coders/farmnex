from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FarmCropCreate(BaseModel):
    farm_id: UUID
    crop_type_id: UUID
    variety: str | None = Field(default=None, max_length=150)
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    area_value: Decimal | None = Field(default=None, ge=0)
    area_unit: str | None = Field(default=None, max_length=30)
    status: str = Field(default="ACTIVE", max_length=30)
    notes: str | None = None
    is_active: bool = True


class FarmCropUpdate(BaseModel):
    farm_id: UUID | None = None
    crop_type_id: UUID | None = None
    variety: str | None = Field(default=None, max_length=150)
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    area_value: Decimal | None = Field(default=None, ge=0)
    area_unit: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, max_length=30)
    notes: str | None = None
    is_active: bool | None = None


class FarmCropResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: UUID
    farmer_id: int
    farm_id: int
    crop_type_id: int
    variety: str | None = None
    sowing_date: date | None = None
    expected_harvest_date: date | None = None
    area_value: Decimal | None = None
    area_unit: str | None = None
    status: str
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
