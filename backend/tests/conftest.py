"""Shared test setup: a test database, a user-with-role helper, a token helper and an HTTP client.

How to use it in a test (mark the module with `pytestmark = pytest.mark.anyio`):

    async def test_something(client, make_user, make_token):
        farmer = await make_user("FARMER")
        response = await client.get(
            "/api/v2/farms", headers={"Authorization": f"Bearer {make_token(farmer)}"}
        )

The database tests need `TEST_DATABASE_URL` (a throwaway Postgres, e.g.
`docker run -p 5433:5432 -e POSTGRES_PASSWORD=test postgres:16` and
`TEST_DATABASE_URL=postgresql://postgres:test@localhost:5433/postgres`). When it is not set they are
skipped. The main Supabase database is never used: a URL that mentions "supabase", or that is
neither on this computer nor named "*test*", stops the run.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from urllib.parse import urlsplit

import pytest

# Make `import app` work even when pytest is started as plain `pytest` instead of `python -m pytest`.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _read_test_database_url() -> str | None:
    """TEST_DATABASE_URL as an asyncpg URL, or None if unset. Refuses anything that could be live."""
    raw = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not raw:
        return None

    parts = urlsplit(raw)
    host = (parts.hostname or "").lower()
    database = parts.path.lstrip("/").lower()

    if "supabase" in raw.lower():
        raise pytest.UsageError("TEST_DATABASE_URL points at Supabase. Tests must never use it.")
    if host not in _LOCAL_HOSTS and "test" not in database:
        raise pytest.UsageError(
            "TEST_DATABASE_URL must be a database on this computer, or one whose name contains 'test'."
        )

    scheme, _, rest = raw.partition("://")
    if scheme in {"postgres", "postgresql"}:
        return f"postgresql+asyncpg://{rest}"
    return raw


def _prepare_environment() -> str | None:
    """Point the app at the test database and safe placeholders BEFORE `app` is imported.

    Values set here win over a developer's local .env, so tests never touch real settings.
    """
    test_database_url = _read_test_database_url()

    # A throwaway key pair, so tests can sign login tokens without the real secrets/ folder.
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    key_dir = tempfile.TemporaryDirectory(prefix="farmnex-test-keys-")
    _prepare_environment.key_dir = key_dir  # keep the folder alive until the run ends
    (Path(key_dir.name) / "private.pem").write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    (Path(key_dir.name) / "public.pem").write_bytes(
        key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

    os.environ.update(
        {
            "ENVIRONMENT": "testing",
            "DATABASE_URL": test_database_url
            or "postgresql+asyncpg://test:test@localhost:5432/farmnex_test_not_configured",
            "JWT_PRIVATE_KEY_PATH": str(Path(key_dir.name) / "private.pem"),
            "JWT_PUBLIC_KEY_PATH": str(Path(key_dir.name) / "public.pem"),
            "SUPABASE_URL": "https://example.invalid",
            "SUPABASE_SECRET_KEY": "test-not-a-real-key",
            "OTP_ENABLED": "false",
            "ENABLE_OTP_LOGIN": "false",
            # Optional components stay off so tests behave the same on every machine.
            "ENABLE_CROP_RESCUE": "false",
            "ENABLE_FORECAST": "false",
            "ENABLE_ROUTE_OPTIMIZER": "false",
            "ENABLE_VOICE_TOOLS": "false",
        }
    )
    os.environ.setdefault("STORAGE_BUCKET", "storage-bucket")

    return test_database_url


TEST_DATABASE_URL = _prepare_environment()


# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


async def _empty_all_tables_except_roles() -> None:
    from sqlalchemy import text

    from app.core.base import Base
    from app.core.database import engine

    tables = [name for name in Base.metadata.tables if name != "roles"]  # CASCADE handles the order
    async with engine.begin() as connection:
        await connection.execute(
            text("TRUNCATE " + ", ".join(f'"{name}"' for name in tables) + " RESTART IDENTITY CASCADE")
        )


async def _create_tables_and_roles() -> None:
    import app.domain_model_registry  # noqa: F401  (registers every model so create_all sees them)
    from app.core.database import close_database, create_tables
    from app.main import seed_default_roles

    await create_tables()
    await seed_default_roles()
    await _empty_all_tables_except_roles()
    await close_database()


@pytest.fixture(scope="session")
def test_database() -> str:
    """Create the tables and the default roles once. Skips the test if TEST_DATABASE_URL is unset."""
    if TEST_DATABASE_URL is None:
        pytest.skip("TEST_DATABASE_URL is not set, so database tests are skipped.")

    asyncio.run(_create_tables_and_roles())
    return TEST_DATABASE_URL


@pytest.fixture
async def db(anyio_backend: str, test_database: str) -> AsyncIterator[None]:
    """A clean database for one test: every table except `roles` is emptied afterwards."""
    yield
    await _empty_all_tables_except_roles()


# ---------------------------------------------------------------------------
# Helpers: users, tokens, HTTP client
# ---------------------------------------------------------------------------


@pytest.fixture
async def make_user(db: None) -> Callable[..., Awaitable]:
    """`await make_user("BUYER")` creates an active user with that role (FARMER, BUYER, ADMIN, ...)."""
    from app.core.database import AsyncSessionLocal
    from app.core.enums import AccountStatus
    from app.models.user import User
    from app.repositories.role_repository import RoleRepository

    async def _make_user(role: str = "FARMER", *, phone_number: str | None = None) -> User:
        async with AsyncSessionLocal() as session:
            role_row = await RoleRepository(session).get_by_name(role)
            if role_row is None:
                raise ValueError(f"Unknown role {role!r}")

            user = User(
                phone_number=phone_number or f"+9199{uuid.uuid4().int % 10**8:08d}",
                role_id=role_row.id,
                account_status=AccountStatus.ACTIVE,
                first_name="Test",
            )
            session.add(user)
            await session.commit()
            await session.refresh(user, attribute_names=["role"])
            return user

    return _make_user


@pytest.fixture
def make_token() -> Callable[..., str]:
    """`make_token(user)` returns a login (access) token for a user made by `make_user`."""
    from app.core.security import create_access_token

    def _make_token(user) -> str:
        return create_access_token(user_id=user.public_id, role=user.role.name)

    return _make_token


@pytest.fixture
async def client(db: None) -> AsyncIterator:
    """An HTTP client that calls the app directly (no server, no startup work)."""
    import httpx

    from app.main import app

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as http_client:
        yield http_client
