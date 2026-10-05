"""FarmNex glue for Crop Rescue (docs/integration/crop-rescue.md).

Loaded by `wiring.py` when ENABLE_CROP_RESCUE=true. The component package is imported inside
`mount` (not at the top) so a bad CR_* setting only disables Crop Rescue, never the backend.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.engine import make_url

from app.api.dependencies.current_user import get_current_user
from app.models.user import User
from app.modules.crops import rescue_code

logger = logging.getLogger(__name__)

# POST /rescue/check runs the spoilage check for EVERY farmer, so only staff may call it.
_CHECK_ROLES = frozenset({"ADMIN", "SUPER_ADMIN", "MANAGER"})

# True once mount() worked, so new listings may start a spoilage timer.
_mounted = False

KG_PER_UNIT = {"kg": 1, "kgs": 1, "quintal": 100, "quintals": 100,
               "ton": 1000, "tons": 1000, "tonne": 1000, "tonnes": 1000}

NOTE_NO_LOCATION = "Add your farm location (Profile → My farms) to get a spoilage timer in Crop Rescue."
NOTE_BAD_UNIT = "The spoilage timer needs the quantity in kg, quintal or ton."
NOTE_FAILED = "Crop Rescue could not start a spoilage timer right now. You can register the lot there by hand."


def _role_name(user: User) -> str | None:
    return user.role.name.upper() if user.role is not None else None


async def _rescue_farmer_id(user: User = Depends(get_current_user)) -> str:
    """The farmer is always the logged-in FARMER; identity never comes from the request."""
    if _role_name(user) != "FARMER":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only farmers can use Crop Rescue.")
    return str(user.public_id)


async def _guard_check_route(request: Request, user: User = Depends(get_current_user)) -> None:
    if request.method == "POST" and request.url.path.rstrip("/").endswith("/rescue/check"):
        if _role_name(user) not in _CHECK_ROLES:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed for your role.")


def _check_database_url() -> None:
    """Crop Rescue is synchronous: it needs its own psycopg URL, never our async DATABASE_URL."""
    raw = os.getenv("CR_DATABASE_URL", "").strip()
    if not raw:
        raise RuntimeError(
            "CR_DATABASE_URL is not set. Use the Supabase session pooler URL in the form "
            "postgresql+psycopg://...:5432/postgres?sslmode=require"
        )
    try:
        url = make_url(raw)
    except Exception:  # SQLAlchemy's message would quote the URL (and the password)
        raise RuntimeError("CR_DATABASE_URL is not a valid database URL.") from None
    if url.drivername != "postgresql+psycopg":
        raise RuntimeError(
            "CR_DATABASE_URL must start with postgresql+psycopg:// (the synchronous driver we "
            "install), not asyncpg, plain postgresql:// or SQLite."
        )


def mount(app: FastAPI) -> None:
    _check_database_url()

    from . import crop_rescue  # imported here on purpose (shared rule 3)

    app.include_router(
        crop_rescue.router,
        prefix="/api/v2",
        dependencies=[Depends(get_current_user), Depends(_guard_check_route)],
    )
    app.dependency_overrides[crop_rescue.current_farmer_id] = _rescue_farmer_id

    global _mounted
    _mounted = True


def _point(lat: Any, lng: Any) -> tuple[float, float] | None:
    """A usable map point, or None (missing, out of range, or 0,0)."""
    if lat is None or lng is None:
        return None
    lat, lng = float(lat), float(lng)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180) or (lat == 0 and lng == 0):
        return None
    return lat, lng


async def start_timer_for_listing(
    listing: Any, user: User, crop: tuple[str, str | None] | None
) -> tuple[str | None, str | None]:
    """Start a Crop Rescue spoilage timer for a farmer's new listing.

    Returns (rescue lot id, None) on success, or (None, a short reason for the farmer) - the reason is
    None when no timer is expected (Crop Rescue off, not a farmer, pre-harvest PRE_BID listing).
    Never raises: a listing must not fail because of Crop Rescue.

    `listing` is the new ProductListing with `farm` loaded; `crop` is (crop_types.name, category).
    """
    if not _mounted or _role_name(user) != "FARMER" or listing.listing_type == "PRE_BID":
        return None, None
    try:
        point = _point(listing.farm.latitude, listing.farm.longitude)
        if point is None:
            return None, NOTE_NO_LOCATION
        factor = KG_PER_UNIT.get((listing.unit or "").strip().lower())
        if factor is None:
            return None, NOTE_BAD_UNIT
        if crop is None:
            return None, NOTE_FAILED

        from . import crop_rescue

        lot_id = await run_in_threadpool(
            crop_rescue.register_lot,
            str(user.public_id),  # same farmer id the Crop Rescue screens use (_rescue_farmer_id)
            crop_code=rescue_code(*crop),
            quantity_kg=float(Decimal(listing.quantity) * factor),
            harvested_at=datetime.now(timezone.utc),  # the app doesn't ask; listed today = harvested today
            lat=point[0],
            lng=point[1],
            floor_price_per_kg=float(Decimal(listing.price) / factor),
        )
        return lot_id, None
    except Exception:
        logger.exception("Crop Rescue: could not start a spoilage timer for listing %s", listing.public_id)
        return None, NOTE_FAILED


def start() -> None:
    from . import crop_rescue

    crop_rescue.start_scheduler()


def stop() -> None:
    from . import crop_rescue

    crop_rescue.stop_scheduler()
