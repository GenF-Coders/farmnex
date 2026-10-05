"""Sign-up with a one-time code: verify the code once, then create the account.

Bug this guards (S37): the code was accepted, but /register/complete refused the server's own
"number verified" pass whenever the configured JWT public key did not match the signing key
(or two server copies' clocks differed). The app showed "code has expired" and no account
was ever created. These tests use in-memory stand-ins, so no database is needed.
"""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
from itertools import count
from types import SimpleNamespace
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import security
from app.core.config import settings
from app.services.auth_service import AuthService
from app.services.otp.exceptions import (
    OTPAlreadyVerifiedError,
    OTPExpiredError,
    OTPInvalidError,
)
from app.services.otp.schemas import (
    OTPProviderStatus,
    OTPProviderVerifyResult,
    OTPSendResult,
)
from app.services.otp.service import OTPService

pytestmark = pytest.mark.anyio

PHONE = "+919876543210"


# ---------------------------------------------------------------------------
# In-memory stand-ins
# ---------------------------------------------------------------------------


class FakeProvider:
    """Like MiniMoth: remembers the last code sent to each phone; a resend replaces it."""

    name = "fake"

    def __init__(self) -> None:
        self.codes: dict[str, str] = {}
        self._next = count(111111)

    async def send_otp(self, *, phone_number: str) -> OTPSendResult:
        self.codes[phone_number] = str(next(self._next))
        return OTPSendResult(
            success=True,
            status=OTPProviderStatus.SENT,
            provider_name=self.name,
            provider_request_id=str(uuid4()),
        )

    async def verify_otp(self, *, phone_number: str, otp: str) -> OTPProviderVerifyResult:
        if self.codes.get(phone_number) != otp:
            raise OTPInvalidError("Invalid OTP.")
        return OTPProviderVerifyResult(verified=True, provider_name=self.name)


class FakeOTPRepository:
    def __init__(self) -> None:
        self.rows: list[SimpleNamespace] = []
        self.session = SimpleNamespace(commit=self._noop)

    @staticmethod
    async def _noop() -> None:
        return None

    async def create(self, *, phone_number, purpose, provider_name, provider_request_id,
                     expires_at, max_attempts=5, resend_count=0, last_sent_at=None):
        row = SimpleNamespace(
            id=len(self.rows) + 1, public_id=uuid4(), phone_number=phone_number, purpose=purpose,
            expires_at=expires_at, verified_at=None, attempt_count=0, max_attempts=max_attempts,
            resend_count=resend_count, last_sent_at=last_sent_at, created_at=last_sent_at,
        )
        self.rows.append(row)
        return row

    def _for(self, phone_number, purpose):
        return [r for r in self.rows if r.phone_number == phone_number and r.purpose == purpose]

    async def get_latest(self, *, phone_number, purpose):
        rows = self._for(phone_number, purpose)
        return rows[-1] if rows else None

    async def get_latest_valid(self, *, phone_number, purpose, now):
        rows = [
            r for r in self._for(phone_number, purpose)
            if r.expires_at > now and r.verified_at is None and r.attempt_count < r.max_attempts
        ]
        return rows[-1] if rows else None

    async def increment_attempt(self, otp_id):
        row = self.rows[otp_id - 1]
        if row.verified_at is None:
            row.attempt_count += 1

    async def mark_verified(self, otp_id, *, verified_at):
        row = self.rows[otp_id - 1]
        if row.verified_at is None:
            row.verified_at = verified_at

    async def invalidate_previous(self, *, phone_number, purpose, invalidated_at):
        for r in self._for(phone_number, purpose):
            if r.verified_at is None:
                r.verified_at = invalidated_at


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: dict[str, SimpleNamespace] = {}
        self.fail_next_create = False

    async def get_by_phone(self, phone_number):
        return self.users.get(phone_number)

    get_by_phone_with_role = get_by_phone

    async def create(self, *, public_id, phone_number, role_id, phone_verified_at, account_status):
        if self.fail_next_create:
            self.fail_next_create = False
            raise RuntimeError("database hiccup")
        user = SimpleNamespace(
            id=len(self.users) + 1, public_id=public_id, phone_number=phone_number,
            role=SimpleNamespace(name="FARMER"), account_status=account_status,
            phone_verified_at=phone_verified_at,
        )
        self.users[phone_number] = user
        return user


class FakeSessionRepository:
    async def count_active_for_user(self, user_id, now):
        return 0

    async def get_active_sessions_for_user(self, *args, **kwargs):
        return []

    async def revoke(self, *args, **kwargs):
        return None

    async def create(self, **kwargs):
        return SimpleNamespace(**kwargs)


class FakeEvents:
    async def create(self, **kwargs):
        return None


class FakeRoles:
    async def get_by_name(self, name):
        return SimpleNamespace(id=1, name=name)


@pytest.fixture
def otp_on(monkeypatch):
    monkeypatch.setattr(settings, "otp_enabled", True)
    monkeypatch.setattr(settings, "enable_registration", True)
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)


@pytest.fixture
def world(otp_on):
    provider = FakeProvider()
    otp_repo = FakeOTPRepository()
    users = FakeUserRepository()
    auth = AuthService(
        user_repository=users,
        role_repository=FakeRoles(),
        session_repository=FakeSessionRepository(),
        auth_event_repository=FakeEvents(),
        otp_service=OTPService(otp_repository=otp_repo, provider=provider),
    )
    return SimpleNamespace(auth=auth, provider=provider, otp_repo=otp_repo, users=users)


def _other_public_key_b64() -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return base64.b64encode(pem).decode("ascii")


# ---------------------------------------------------------------------------
# The five sign-up cases
# ---------------------------------------------------------------------------


async def test_correct_code_once_creates_the_account(world):
    await world.auth.request_registration_otp(phone_number=PHONE)
    proof = await world.auth.verify_registration_otp(
        phone_number=PHONE, otp=world.provider.codes[PHONE]
    )
    user, access, refresh, _ = await world.auth.complete_registration(
        registration_token=proof["registration_token"], role_name="FARMER"
    )
    assert user.phone_number == PHONE
    assert access and refresh


async def test_same_code_twice_is_rejected_cleanly(world):
    await world.auth.request_registration_otp(phone_number=PHONE)
    code = world.provider.codes[PHONE]
    await world.auth.verify_registration_otp(phone_number=PHONE, otp=code)

    with pytest.raises(OTPAlreadyVerifiedError):
        await world.auth.verify_registration_otp(phone_number=PHONE, otp=code)


async def test_expired_code_is_rejected(world):
    await world.auth.request_registration_otp(phone_number=PHONE)
    world.otp_repo.rows[-1].expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)

    with pytest.raises(OTPExpiredError):
        await world.auth.verify_registration_otp(
            phone_number=PHONE, otp=world.provider.codes[PHONE]
        )


async def test_create_fails_then_try_again_works_without_a_new_code(world):
    await world.auth.request_registration_otp(phone_number=PHONE)
    proof = await world.auth.verify_registration_otp(
        phone_number=PHONE, otp=world.provider.codes[PHONE]
    )

    world.users.fail_next_create = True
    with pytest.raises(RuntimeError):
        await world.auth.complete_registration(
            registration_token=proof["registration_token"], role_name="FARMER"
        )

    # "Try again" sends the same proof only; no code is checked again.
    user, *_ = await world.auth.complete_registration(
        registration_token=proof["registration_token"], role_name="FARMER"
    )
    assert user.phone_number == PHONE
    assert len(world.otp_repo.rows) == 1


async def test_resend_kills_the_old_code_and_the_new_code_works(world):
    await world.auth.request_registration_otp(phone_number=PHONE)
    old_code = world.provider.codes[PHONE]
    await world.auth.resend_registration_otp(phone_number=PHONE)
    new_code = world.provider.codes[PHONE]
    assert new_code != old_code

    with pytest.raises(OTPInvalidError):
        await world.auth.verify_registration_otp(phone_number=PHONE, otp=old_code)

    proof = await world.auth.verify_registration_otp(phone_number=PHONE, otp=new_code)
    user, *_ = await world.auth.complete_registration(
        registration_token=proof["registration_token"], role_name="FARMER"
    )
    assert user.phone_number == PHONE


# ---------------------------------------------------------------------------
# The root cause: the server must accept its own "number verified" pass
# ---------------------------------------------------------------------------


async def test_proof_accepted_even_if_public_key_setting_is_wrong(world, monkeypatch):
    """Production case: JWT_PUBLIC_KEY_B64 is not the partner of the signing key."""
    monkeypatch.setattr(settings, "jwt_public_key_b64", _other_public_key_b64())
    assert security.public_key_matches_private_key() is False

    await world.auth.request_registration_otp(phone_number=PHONE)
    proof = await world.auth.verify_registration_otp(
        phone_number=PHONE, otp=world.provider.codes[PHONE]
    )
    user, *_ = await world.auth.complete_registration(
        registration_token=proof["registration_token"], role_name="FARMER"
    )
    assert user.phone_number == PHONE


async def test_proof_accepted_when_server_clocks_differ_a_little(world, monkeypatch):
    """Verify ran on a copy whose clock is 5 s ahead; complete runs on this one."""
    real_datetime = security.datetime

    class AheadClock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return real_datetime.now(tz) + timedelta(seconds=5)

    await world.auth.request_registration_otp(phone_number=PHONE)
    monkeypatch.setattr(security, "datetime", AheadClock)
    proof = await world.auth.verify_registration_otp(
        phone_number=PHONE, otp=world.provider.codes[PHONE]
    )
    monkeypatch.setattr(security, "datetime", real_datetime)

    user, *_ = await world.auth.complete_registration(
        registration_token=proof["registration_token"], role_name="FARMER"
    )
    assert user.phone_number == PHONE


async def test_a_bad_proof_does_not_say_expired(world, caplog):
    with pytest.raises(ValueError) as error:
        await world.auth.complete_registration(registration_token="not-a-token", role_name="FARMER")
    assert "expired" not in str(error.value).lower()
    assert "Registration token rejected" in caplog.text


async def test_access_token_cannot_be_used_as_a_registration_proof(world):
    access = security.create_access_token(user_id=uuid4(), role="FARMER")
    with pytest.raises(ValueError):
        await world.auth.complete_registration(registration_token=access, role_name="FARMER")
