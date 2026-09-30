"""FarmNex glue for Crop Rescue (docs/integration/crop-rescue.md).

Loaded by `wiring.py` when ENABLE_CROP_RESCUE=true. The component package is imported inside
`mount` (not at the top) so a bad CR_* setting only disables Crop Rescue, never the backend.
"""

from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI, HTTPException, Request, status
from sqlalchemy.engine import make_url

from app.api.dependencies.current_user import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

# POST /rescue/check runs the spoilage check for EVERY farmer, so only staff may call it.
_CHECK_ROLES = frozenset({"ADMIN", "SUPER_ADMIN", "MANAGER"})


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


def start() -> None:
    from . import crop_rescue

    crop_rescue.start_scheduler()


def stop() -> None:
    from . import crop_rescue

    crop_rescue.stop_scheduler()
