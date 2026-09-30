"""Vehicle endpoints for drivers (docs/integration/route-optimizer.md, "Host endpoints we add").

Mounted at /api/v2/logistics by `routes_host.mount()` (with login), so this file is only imported
once the route optimizer is switched on and its database URL is valid. `rt_vehicles` is the
source of truth for vehicles; there is no core vehicles table.

Identity comes only from the login token: the driver is always the logged-in user, and clients
can't send driver ids, owner role or status.
"""

from __future__ import annotations

from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from farmnex_routes import upsert_vehicle
from farmnex_routes.db import session_scope
from farmnex_routes.models import RtVehicle
from farmnex_routes.schemas import VehicleOut
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles
from app.models.user import User

router = APIRouter(tags=["Logistics"])

MAX_VEHICLES_PER_USER = 5

VehicleType = Literal["pickup", "tempo", "mini_truck", "truck"]


class VehicleCreate(BaseModel):
    vehicle_number: str = Field(min_length=4, max_length=20, examples=["MH12AB1234"])
    vehicle_type: VehicleType
    capacity_kg: float = Field(gt=0, le=40000)
    refrigerated: bool = False
    rate_per_ton_km: float = Field(gt=0, description="Rs per tonne per km")
    base_lat: float = Field(ge=-90, le=90)
    base_lng: float = Field(ge=-180, le=180)
    base_label: str | None = Field(None, max_length=200)


class VehicleUpdate(BaseModel):
    """Only these fields can change; leave a field out to keep it."""

    vehicle_number: str | None = Field(None, min_length=4, max_length=20)
    vehicle_type: VehicleType | None = None
    capacity_kg: float | None = Field(None, gt=0, le=40000)
    refrigerated: bool | None = None
    rate_per_ton_km: float | None = Field(None, gt=0)
    base_lat: float | None = Field(None, ge=-90, le=90)
    base_lng: float | None = Field(None, ge=-180, le=180)
    base_label: str | None = Field(None, max_length=200)


def _driver_name(user: User) -> str | None:
    name = " ".join(part for part in (user.first_name, user.surname) if part)
    return name[:120] or None


def _create_vehicle(fields: dict) -> RtVehicle | None:
    with session_scope() as session:
        owned = session.scalar(
            select(func.count()).select_from(RtVehicle).where(RtVehicle.driver_user_id == fields["driver_user_id"])
        )
        if owned >= MAX_VEHICLES_PER_USER:
            return None
        return upsert_vehicle(session, str(uuid4()), **fields)


def _update_vehicle(vehicle_id: str, me: str, fields: dict) -> RtVehicle | None:
    with session_scope() as session:
        vehicle = session.get(RtVehicle, vehicle_id)
        if vehicle is None or vehicle.driver_user_id != me:
            return None
        if vehicle.status == "on_trip":
            raise HTTPException(409, "Finish or cancel the current trip before editing the vehicle.")
        return upsert_vehicle(session, vehicle_id, **fields)


def _list_vehicles(me: str) -> list[RtVehicle]:
    with session_scope() as session:
        return list(
            session.scalars(
                select(RtVehicle).where(RtVehicle.driver_user_id == me).order_by(RtVehicle.created_at)
            )
        )


@router.post("/vehicles", response_model=VehicleOut, status_code=201)
async def register_vehicle(
    body: VehicleCreate,
    user: User = Depends(require_roles("DELIVERY_AGENT", "FARMER")),
):
    """A driver registers a truck. A farmer can register their own (self-delivery)."""
    fields = body.model_dump()
    fields.update(
        driver_user_id=str(user.public_id),
        driver_name=_driver_name(user),
        driver_phone=user.phone_number,
        owner_role="farmer" if user.role.name.upper() == "FARMER" else "transporter",
    )
    vehicle = await run_in_threadpool(_create_vehicle, fields)
    if vehicle is None:
        raise HTTPException(409, f"You can register at most {MAX_VEHICLES_PER_USER} vehicles.")
    return vehicle


@router.patch("/vehicles/{vehicle_id}", response_model=VehicleOut)
async def update_vehicle(
    vehicle_id: str,
    body: VehicleUpdate,
    user: User = Depends(get_current_user),
):
    """Change rate, capacity, base... Only that vehicle's driver; anyone else gets 404."""
    fields = body.model_dump(exclude_none=True)
    vehicle = await run_in_threadpool(_update_vehicle, vehicle_id, str(user.public_id), fields)
    if vehicle is None:
        raise HTTPException(404, "Vehicle not found.")
    return vehicle


@router.get("/my-vehicles", response_model=list[VehicleOut])
async def my_vehicles(user: User = Depends(get_current_user)):
    return await run_in_threadpool(_list_vehicles, str(user.public_id))
