"""Automatic Crop Rescue timer for new listings: skip rules, conversions, never fails the listing.

No database: `crop_rescue.register_lot` is replaced by a fake.
"""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules import crop_rescue, crop_rescue_host
from app.modules.crop_rescue.schemas import LotOut

pytestmark = pytest.mark.anyio

PUNE = (Decimal("18.5204"), Decimal("73.8567"))


def _user(role: str = "FARMER"):
    return SimpleNamespace(public_id=uuid4(), role=SimpleNamespace(name=role))


def _listing(*, listing_type="FIXED_PRICE", unit="kg", quantity="500", price="24", lat=PUNE[0], lng=PUNE[1]):
    return SimpleNamespace(
        public_id=uuid4(),
        listing_type=listing_type,
        unit=unit,
        quantity=Decimal(quantity),
        price=Decimal(price),
        farm=SimpleNamespace(latitude=lat, longitude=lng),
    )


@pytest.fixture
def calls(monkeypatch):
    """Crop Rescue is mounted; register_lot records its arguments and returns a lot id."""
    seen: list[tuple[tuple, dict]] = []

    def fake_register_lot(*args, **kwargs):
        seen.append((args, kwargs))
        return "lot-1"

    monkeypatch.setattr(crop_rescue_host, "_mounted", True)
    monkeypatch.setattr(crop_rescue, "register_lot", fake_register_lot)
    return seen


async def test_farmer_listing_starts_a_timer_with_farmer_id_from_login(calls):
    user = _user()
    lot_id, note = await crop_rescue_host.start_timer_for_listing(_listing(), user, ("Tomato", "Vegetable"))
    assert (lot_id, note) == ("lot-1", None)
    (args, kwargs), = calls
    assert args == (str(user.public_id),)
    assert kwargs["crop_code"] == "tomato"
    assert kwargs["quantity_kg"] == 500.0
    assert kwargs["floor_price_per_kg"] == 24.0
    assert (kwargs["lat"], kwargs["lng"]) == (float(PUNE[0]), float(PUNE[1]))


async def test_quintal_and_ton_are_converted_to_kg(calls):
    await crop_rescue_host.start_timer_for_listing(
        _listing(unit="Quintal", quantity="2", price="2400"), _user(), ("Wheat", "Cereal")
    )
    await crop_rescue_host.start_timer_for_listing(
        _listing(unit="ton", quantity="1.5", price="3000"), _user(), ("Sugarcane", "Cash Crop")
    )
    (_, wheat), (_, cane) = calls
    assert (wheat["crop_code"], wheat["quantity_kg"], wheat["floor_price_per_kg"]) == ("wheat", 200.0, 24.0)
    assert (cane["crop_code"], cane["quantity_kg"], cane["floor_price_per_kg"]) == ("sugarcane", 1500.0, 3.0)


async def test_unlisted_crop_uses_the_category_estimate(calls):
    await crop_rescue_host.start_timer_for_listing(_listing(), _user(), ("Papaya", "Fruit"))
    assert calls[0][1]["crop_code"] == "est_fruit"


@pytest.mark.parametrize(
    "listing, user",
    [
        (_listing(listing_type="PRE_BID"), _user()),  # pre-harvest: nothing to spoil yet
        (_listing(), _user("VENDOR")),
        (_listing(), _user("BUYER")),
    ],
)
async def test_no_timer_and_no_note_when_none_is_expected(calls, listing, user):
    assert await crop_rescue_host.start_timer_for_listing(listing, user, ("Tomato", "Vegetable")) == (None, None)
    assert calls == []


async def test_no_timer_when_crop_rescue_is_off(calls, monkeypatch):
    monkeypatch.setattr(crop_rescue_host, "_mounted", False)
    assert await crop_rescue_host.start_timer_for_listing(_listing(), _user(), ("Tomato", None)) == (None, None)
    assert calls == []


@pytest.mark.parametrize("lat, lng", [(None, None), (PUNE[0], None), (Decimal(0), Decimal(0))])
async def test_farm_without_location_gives_a_note(calls, lat, lng):
    result = await crop_rescue_host.start_timer_for_listing(_listing(lat=lat, lng=lng), _user(), ("Tomato", None))
    assert result == (None, crop_rescue_host.NOTE_NO_LOCATION)
    assert calls == []


async def test_unknown_unit_gives_a_note(calls):
    result = await crop_rescue_host.start_timer_for_listing(_listing(unit="dozen"), _user(), ("Banana", "Fruit"))
    assert result == (None, crop_rescue_host.NOTE_BAD_UNIT)
    assert calls == []


async def test_crop_rescue_error_never_reaches_the_listing(monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError("database down")

    monkeypatch.setattr(crop_rescue_host, "_mounted", True)
    monkeypatch.setattr(crop_rescue, "register_lot", broken)
    result = await crop_rescue_host.start_timer_for_listing(_listing(), _user(), ("Tomato", None))
    assert result == (None, crop_rescue_host.NOTE_FAILED)


def _lot(crop_code: str) -> dict:
    now = "2026-10-05T06:00:00Z"
    return {
        "id": "x", "crop_code": crop_code, "quantity_kg": 1, "harvested_at": now, "lat": 1, "lng": 1,
        "storage_mode": "ambient", "floor_price_per_kg": 1, "temperature_c": None, "freshness_used": 0,
        "remaining_hours": 1, "spoil_eta": None, "status": "fresh", "last_checked_at": now, "created_at": now,
    }


def test_lot_response_says_whether_the_shelf_life_is_an_estimate():
    assert LotOut.model_validate(_lot("tomato")).model_dump()["estimate"] is False
    assert LotOut.model_validate(_lot("wheat")).model_dump()["estimate"] is True
