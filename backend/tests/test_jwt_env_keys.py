"""Login keys can come from environment variables (JWT_*_KEY_B64) instead of files.

FastAPI Cloud never receives the git-ignored secrets/ folder, so production passes
the keys as one-line base64 values. These tests prove both ways work.
"""

import base64
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import security
from app.core.config import Settings, settings


def _new_pair_b64() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return (
        base64.b64encode(private_pem).decode("ascii"),
        base64.b64encode(public_pem).decode("ascii"),
    )


def test_file_keys_still_work():
    token = security.create_access_token(user_id=uuid4(), role="FARMER")
    assert security.is_access_token(security.decode_token(token))


def test_env_keys_sign_and_verify(monkeypatch):
    private_b64, public_b64 = _new_pair_b64()
    monkeypatch.setattr(settings, "jwt_private_key_b64", private_b64)
    monkeypatch.setattr(settings, "jwt_public_key_b64", public_b64)
    # Point the file paths nowhere: the env values must be what's used.
    monkeypatch.setattr(settings, "jwt_private_key_path", "does/not/exist.pem")
    monkeypatch.setattr(settings, "jwt_public_key_path", "does/not/exist.pem")

    user_id = uuid4()
    token = security.create_access_token(user_id=user_id, role="BUYER")
    payload = security.decode_token(token)

    assert security.is_access_token(payload)
    assert payload["sub"] == str(user_id)


def test_env_key_wins_over_file(monkeypatch):
    """A token signed with the file key must not verify with a different env public key."""
    token = security.create_access_token(user_id=uuid4(), role="FARMER")
    _, other_public_b64 = _new_pair_b64()
    monkeypatch.setattr(settings, "jwt_public_key_b64", other_public_b64)

    with pytest.raises(Exception):
        security.decode_token(token)


def test_bad_base64_gives_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "jwt_private_key_b64", "not base64 !!!")
    with pytest.raises(RuntimeError, match="JWT_PRIVATE_KEY_B64"):
        security.create_access_token(user_id=uuid4(), role="FARMER")


def test_base64_that_is_not_a_key_is_rejected(monkeypatch):
    monkeypatch.setattr(
        settings, "jwt_private_key_b64", base64.b64encode(b"hello").decode("ascii")
    )
    with pytest.raises(RuntimeError, match="PEM"):
        security.create_access_token(user_id=uuid4(), role="FARMER")


def test_production_accepts_env_keys_without_paths():
    private_b64, public_b64 = _new_pair_b64()
    base = settings.model_dump()
    base.update(
        environment="production",
        debug=False,
        secure_cookies=True,
        enable_security_headers=True,
        trust_proxy_headers=False,
        db_echo=False,
        audit_log_enabled=True,
        jwt_private_key_path="",
        jwt_public_key_path="",
        jwt_private_key_b64=private_b64,
        jwt_public_key_b64=public_b64,
    )
    Settings(**base)  # must not raise


def test_production_needs_some_key():
    base = settings.model_dump()
    base.update(
        environment="production",
        debug=False,
        secure_cookies=True,
        enable_security_headers=True,
        trust_proxy_headers=False,
        db_echo=False,
        audit_log_enabled=True,
        jwt_private_key_path="",
        jwt_public_key_path="",
        jwt_private_key_b64=None,
        jwt_public_key_b64=None,
    )
    with pytest.raises(ValueError, match="JWT private key"):
        Settings(**base)


def test_damaged_public_key_env_falls_back_to_private_key(monkeypatch):
    """Production case (S37): JWT_PUBLIC_KEY_B64 was cut off when pasted ("Incorrect padding").

    Every logged-in request crashed with a 500. The server must use the public half of its
    own private key instead, and still report the bad setting.
    """
    private_b64, public_b64 = _new_pair_b64()
    monkeypatch.setattr(settings, "jwt_private_key_b64", private_b64)
    monkeypatch.setattr(settings, "jwt_public_key_b64", public_b64[:-7])  # cut off

    user_id = uuid4()
    token = security.create_access_token(user_id=user_id, role="FARMER")

    assert security.decode_token(token)["sub"] == str(user_id)
    assert security.public_key_matches_private_key() is False
