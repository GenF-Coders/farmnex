"""FarmNex Crop Rescue: a drop-in FastAPI router module.

Public surface: `router, start_scheduler, stop_scheduler, settings,
configure, current_farmer_id, register_lot`. The host touches only these seven names.
Everything else in this package is an internal implementation detail.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Callable

from . import db as _db
from . import service as _service
from .api import router
from .config import settings
from .deps import current_farmer_id
from .scheduler import start_scheduler, stop_scheduler

if TYPE_CHECKING:
    from sqlalchemy import Engine

    from .repository import AlertRecord

__all__ = [
    "router",
    "start_scheduler",
    "stop_scheduler",
    "settings",
    "configure",
    "current_farmer_id",
    "register_lot",
]


def configure(engine: "Engine | None" = None, on_alert: "Callable[[AlertRecord], None] | None" = None) -> None:
    """Wire the host's own SQLAlchemy engine and/or an alert callback (e.g. an
    FCM push) into this module. Both are optional; call with only the one
    you want to set.

        crop_rescue.configure(engine=app_engine)                # share the pool
        crop_rescue.configure(on_alert=send_fcm_push)            # optional push
    """
    if engine is not None:
        _db.configure(engine=engine)
    if on_alert is not None:
        _service.configure_on_alert(on_alert)


def register_lot(
    farmer_id: str,
    *,
    crop_code: str,
    quantity_kg: float,
    harvested_at: datetime,
    lat: float,
    lng: float,
    floor_price_per_kg: float,
    storage_mode: str = "ambient",
) -> str:
    """Register a lot from host code (e.g. when a farmer lists produce) and return its id.

    Same rules as POST /rescue/lots: the first freshness check runs at once. Synchronous —
    call it from async code with `run_in_threadpool`. `farmer_id` must come from the login.
    """
    lot = _service.create_lot(
        _db.get_engine(),
        farmer_id,
        crop_code=crop_code,
        quantity_kg=quantity_kg,
        harvested_at=harvested_at,
        lat=lat,
        lng=lng,
        storage_mode=storage_mode,
        floor_price_per_kg=floor_price_per_kg,
        temperature_c=None,
        now=datetime.now(timezone.utc),
    )
    return lot.id
