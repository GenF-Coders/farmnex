from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
    VerifyMismatchError,
)

from app.core.config import settings


# ============================================================
# PROJECT PATHS
# ============================================================

# backend/
# ├── app/
# │   └── core/
# │       └── security.py
# ├── secrets/
# │   ├── jwt_private.pem
# │   └── jwt_public.pem
# └── ...

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_key_path(configured_path: str) -> Path:
    """Resolve absolute paths as-is and relative paths from project root."""
    path = Path(configured_path)

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path


# ============================================================
# ARGON2 PASSWORD / PIN / SECRET HASHING
# ============================================================

_password_hasher = PasswordHasher()


def hash_value(value: str) -> str:
    """Hash a sensitive value with Argon2id.

    Used for PINs, refresh tokens, and other authentication secrets.
    Plain values must never be stored in the database.
    """
    if not value:
        raise ValueError("Value to hash cannot be empty.")

    return _password_hasher.hash(value)


def verify_value(hashed_value: str, plain_value: str) -> bool:
    """Verify a plain value against an Argon2id hash."""
    if not hashed_value or not plain_value:
        return False

    try:
        return _password_hasher.verify(hashed_value, plain_value)
    except (
        VerifyMismatchError,
        VerificationError,
        InvalidHashError,
    ):
        return False


# ============================================================
# JWT KEY LOADING
# ============================================================

def _load_private_key() -> str:
    """Load the RSA private key used to sign JWTs."""
    path = _resolve_key_path(settings.jwt_private_key_path)

    if not path.is_file():
        raise RuntimeError(f"JWT private key not found: {path}")

    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Unable to read JWT private key: {path}"
        ) from exc


def _load_public_key() -> str:
    """Load the RSA public key used to verify JWTs."""
    path = _resolve_key_path(settings.jwt_public_key_path)

    if not path.is_file():
        raise RuntimeError(f"JWT public key not found: {path}")

    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Unable to read JWT public key: {path}"
        ) from exc


# ============================================================
# JWT ENCODING
# ============================================================

def _encode_token(*, payload: dict[str, Any]) -> str:
    """Sign and encode a JWT using the configured RSA private key."""
    private_key = _load_private_key()

    return jwt.encode(
        payload,
        private_key,
        algorithm=settings.jwt_algorithm,
    )


# ============================================================
# ACCESS TOKEN
# ============================================================

def create_access_token(*, user_id: UUID, role: str) -> str:
    """Create a short-lived access JWT."""
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "access",
        "role": role,
        "jti": str(uuid4()),
        "iat": now,
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    return _encode_token(payload=payload)


# ============================================================
# REFRESH TOKEN
# ============================================================

def create_refresh_token(
    *,
    user_id: UUID,
    session_id: UUID,
    token_family: UUID,
) -> str:
    """Create a long-lived refresh JWT.

    The raw refresh token must never be stored in the database.
    Only its Argon2 hash should be stored.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        days=settings.refresh_token_expire_days
    )

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "session_id": str(session_id),
        "token_family": str(token_family),
        "jti": str(uuid4()),
        "iat": now,
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    return _encode_token(payload=payload)


# ============================================================
# REGISTRATION TOKEN
# ============================================================

def create_registration_token(*, phone_number: str) -> str:
    """Create a short-lived proof that registration OTP was verified.

    This token is NOT an access token and NOT a refresh token.
    It only authorizes the registration-completion step.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(
        minutes=settings.registration_token_expire_minutes
    )

    payload: dict[str, Any] = {
        "sub": phone_number,
        "phone_number": phone_number,
        "type": "registration",
        "jti": str(uuid4()),
        "iat": now,
        "exp": expires_at,
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
    }

    return _encode_token(payload=payload)


# ============================================================
# JWT DECODING / VERIFICATION
# ============================================================

def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT.

    Verifies signature, expiration, issuer, and audience.
    Token-purpose validation is performed by the caller.
    """
    if not token:
        raise ValueError("JWT token cannot be empty.")

    public_key = _load_public_key()

    payload = jwt.decode(
        token,
        public_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
        audience=settings.jwt_audience,
    )

    if not isinstance(payload, dict):
        raise ValueError("Invalid JWT payload.")

    return payload


# ============================================================
# TOKEN TYPE VALIDATION
# ============================================================

def is_access_token(payload: dict[str, Any]) -> bool:
    return payload.get("type") == "access"


def is_refresh_token(payload: dict[str, Any]) -> bool:
    return payload.get("type") == "refresh"


def is_registration_token(payload: dict[str, Any]) -> bool:
    return payload.get("type") == "registration"
