"""F3: `require_roles` lets listed roles in and gives everyone else 403.

The first tests fake the logged-in user (no database needed). The last ones use real users and
login tokens from conftest (they need TEST_DATABASE_URL and are skipped without it).
"""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest
from fastapi import Depends, FastAPI

from app.api.dependencies.current_user import get_current_user
from app.api.dependencies.roles import require_roles

pytestmark = pytest.mark.anyio


def _app_with_admin_route() -> FastAPI:
    app = FastAPI()

    @app.get("/admin-only")
    async def admin_only(user=Depends(require_roles("ADMIN", "SUPER_ADMIN"))):
        return {"ok": True}

    return app


def _fake_user(role_name: str | None):
    return SimpleNamespace(role=None if role_name is None else SimpleNamespace(name=role_name))


async def _get_as(role_name: str | None) -> httpx.Response:
    app = _app_with_admin_route()
    app.dependency_overrides[get_current_user] = lambda: _fake_user(role_name)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        return await c.get("/admin-only")


@pytest.mark.parametrize("role_name", ["ADMIN", "SUPER_ADMIN", "admin"])
async def test_listed_role_is_allowed(role_name: str) -> None:
    response = await _get_as(role_name)

    assert response.status_code == 200


@pytest.mark.parametrize("role_name", ["BUYER", "FARMER", "VENDOR", None])
async def test_other_role_is_forbidden(role_name: str | None) -> None:
    response = await _get_as(role_name)

    assert response.status_code == 403


async def test_no_token_is_401_not_403() -> None:
    app = _app_with_admin_route()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        response = await c.get("/admin-only")

    assert response.status_code == 401


def test_needs_at_least_one_role() -> None:
    with pytest.raises(ValueError):
        require_roles()


# --- with real users and tokens (test database) -------------------------------------------------


async def _get_with_real_token(user, make_token) -> httpx.Response:
    app = _app_with_admin_route()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        return await c.get("/admin-only", headers={"Authorization": f"Bearer {make_token(user)}"})


async def test_real_buyer_gets_403(make_user, make_token) -> None:
    buyer = await make_user("BUYER")

    response = await _get_with_real_token(buyer, make_token)

    assert response.status_code == 403


async def test_real_admin_is_allowed(make_user, make_token) -> None:
    admin = await make_user("ADMIN")

    response = await _get_with_real_token(admin, make_token)

    assert response.status_code == 200
