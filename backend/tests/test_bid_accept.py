"""F12b bids and the pre-bid winner (S19).

Rules (FIX_PLAN F12 prototype minimum + STATUS "Wave 3 decisions" / "Pre-flight defaults"):
- A new bid must beat the highest open bid by the event's `minimum_increment`; bids on one event are
  placed one at a time (row lock), so two bids at once can't both pass with the same amount.
- `POST /bids/{id}/accept`: only the farmer who opened the event (anyone else gets 404). The event
  closes (`CLOSED`, `winner_bid_id` = the bid's public UUID), the bid is `WON`, the other open bids
  `LOST`, and the buyer gets one `PLACED` order at the bid price (amount = price per unit) for the
  bid's quantity, or all available stock when the bid names none.
- No double winners: two accepts at the same time → one winner, one order. Accepting the same bid
  again (e.g. the same `Idempotency-Key`) returns the same result; another bid afterwards → 409.
The first tests need no database; the rest need TEST_DATABASE_URL.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

import app.main as main_module

pytestmark = pytest.mark.anyio

EVENTS = "/api/v2/bid-events"
BIDS = "/api/v2/bids"


def _auth(user, make_token, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {make_token(user)}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


# ---------------------------------------------------------------------------
# No database: routes and response shapes
# ---------------------------------------------------------------------------


def test_accept_route_exists_and_takes_idempotency_key():
    operation = main_module.app.openapi()["paths"]["/api/v2/bids/{public_id}/accept"]["post"]
    assert "Idempotency-Key" in {p["name"] for p in operation.get("parameters", [])}
    assert "requestBody" not in operation  # nothing to send: the bid id is in the path


def test_event_response_shows_winner_as_uuid():
    from app.schemas.bid_event_schema import BidEventResponse

    assert "winner_bid_id" in BidEventResponse.model_fields
    assert BidEventResponse.model_fields["winner_bid_id"].annotation == uuid.UUID | None


def test_order_number_is_tied_to_the_bid():
    from types import SimpleNamespace

    from app.services.bid_service import bid_order_number

    bid = SimpleNamespace(public_id=uuid.UUID("12345678-1234-5678-1234-567812345678"))
    number = bid_order_number(bid)
    assert number == "BID-12345678123456781234567812345678"
    assert len(number) <= 50  # orders.order_number is String(50)


async def test_accept_needs_login(client):
    response = await client.post(f"{BIDS}/{uuid.uuid4()}/accept")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


async def _seed_listing(farmer, *, price="20.00", quantity="100") -> uuid.UUID:
    """A farm, crop, batch and ACTIVE pre-bid listing owned by `farmer`. Returns the listing public id."""
    from app.core.database import AsyncSessionLocal
    from app.models.crop_batch import CropBatch
    from app.models.crop_type import CropType
    from app.models.farm import Farm
    from app.models.farm_crop import FarmCrop
    from app.models.product_listing import ProductListing

    async with AsyncSessionLocal() as session:
        farm = Farm(user_id=farmer.id, farm_name="Test farm", address_line_1="Road 1",
                    state="Maharashtra", postal_code="411001")
        crop_type = CropType(name=f"Tomato-{uuid.uuid4().hex[:8]}", default_unit="kg")
        session.add_all([farm, crop_type])
        await session.flush()
        farm_crop = FarmCrop(farmer_id=farmer.id, farm_id=farm.id, crop_type_id=crop_type.id)
        session.add(farm_crop)
        await session.flush()
        batch = CropBatch(farm_crop_id=farm_crop.id, batch_code=f"B-{uuid.uuid4().hex[:10]}",
                          quantity=Decimal(quantity), available_quantity=Decimal(quantity), unit="kg")
        session.add(batch)
        await session.flush()
        listing = ProductListing(
            seller_id=farmer.id, farm_id=farm.id, crop_batch_id=batch.id, title="Tomatoes, pre-harvest",
            listing_type="PRE_BID", price=Decimal(price), quantity=Decimal(quantity),
            available_quantity=Decimal(quantity), unit="kg", status="ACTIVE",
        )
        session.add(listing)
        await session.commit()
        return listing.public_id


async def _seed_address(user) -> None:
    from app.core.database import AsyncSessionLocal
    from app.models.address import Address

    async with AsyncSessionLocal() as session:
        session.add(Address(user_id=user.id, address_line_1="Market Road 5", city="Pune", state="Maharashtra",
                            postal_code="411002", latitude=Decimal("18.5204"), longitude=Decimal("73.8567"),
                            is_default=True))
        await session.commit()


async def _available(listing_id) -> Decimal:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.product_listing import ProductListing

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ProductListing.available_quantity).where(ProductListing.public_id == listing_id)
        )
        return result.scalar_one()


async def _order_count() -> int:
    from sqlalchemy import func, select

    from app.core.database import AsyncSessionLocal
    from app.models.order import Order

    async with AsyncSessionLocal() as session:
        return int((await session.execute(select(func.count()).select_from(Order))).scalar_one())


async def _bid_statuses(event_id: str) -> dict[str, str]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.bid import Bid
    from app.models.bid_event import BidEvent

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Bid.public_id, Bid.status).join(BidEvent, BidEvent.id == Bid.bid_event_id)
            .where(BidEvent.public_id == uuid.UUID(event_id))
        )
        return {str(public_id): status for public_id, status in result}


async def _bid(client, make_token, user, event_id: str, amount: str, **extra):
    return await client.post(
        BIDS, json={"bid_event_id": event_id, "amount": amount, **extra}, headers=_auth(user, make_token)
    )


async def _accept(client, make_token, user, bid_id: str, key: str | None = None):
    return await client.post(f"{BIDS}/{bid_id}/accept", headers=_auth(user, make_token, key))


@pytest.fixture
async def auction(client, make_user, make_token):
    """A farmer's open event (start 18.00, step 0.50) on 100 kg, and two buyers with addresses."""
    farmer = await make_user("FARMER")
    buyer = await make_user("BUYER")
    rival = await make_user("BUYER")
    await _seed_address(buyer)
    await _seed_address(rival)
    listing_id = await _seed_listing(farmer)
    now = datetime.now(timezone.utc)
    response = await client.post(
        EVENTS,
        json={"listing_id": str(listing_id), "starts_at": (now - timedelta(hours=1)).isoformat(),
              "ends_at": (now + timedelta(days=7)).isoformat(), "starting_price": "18.00",
              "minimum_increment": "0.50"},
        headers=_auth(farmer, make_token),
    )
    assert response.status_code == 201, response.text
    return {"farmer": farmer, "buyer": buyer, "rival": rival, "listing": listing_id, "event": response.json()["public_id"]}


# ---------------------------------------------------------------------------
# Minimum increment
# ---------------------------------------------------------------------------


async def test_bid_must_beat_highest_by_minimum_increment(client, make_token, auction):
    a = auction
    assert (await _bid(client, make_token, a["buyer"], a["event"], "19.00")).status_code == 201
    too_low = await _bid(client, make_token, a["rival"], a["event"], "19.49")
    assert too_low.status_code == 422
    assert "19.50" in too_low.json()["detail"]
    assert (await _bid(client, make_token, a["rival"], a["event"], "19.50")).status_code == 201


async def test_two_bids_at_the_same_time_cannot_both_pass(client, make_token, auction):
    a = auction
    assert (await _bid(client, make_token, a["buyer"], a["event"], "19.00")).status_code == 201
    responses = await asyncio.gather(
        _bid(client, make_token, a["buyer"], a["event"], "20.00"),
        _bid(client, make_token, a["rival"], a["event"], "20.00"),
    )
    assert sorted(r.status_code for r in responses) == [201, 422]


async def test_bid_quantity_cannot_exceed_what_is_on_offer(client, make_token, auction):
    a = auction
    response = await _bid(client, make_token, a["buyer"], a["event"], "19.00", quantity="101")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Accept
# ---------------------------------------------------------------------------


async def test_farmer_accepts_bid_closes_event_and_creates_order(client, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "19.00", quantity="40")).json()
    rival_bid = (await _bid(client, make_token, a["rival"], a["event"], "19.50", quantity="10")).json()

    response = await _accept(client, make_token, a["farmer"], bid["public_id"])

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["bid_event"]["status"] == "CLOSED"
    assert body["bid_event"]["winner_bid_id"] == bid["public_id"]
    assert body["bid"]["public_id"] == bid["public_id"] and body["bid"]["status"] == "WON"
    order = body["order"]
    assert order["status"] == "PLACED"
    assert order["order_number"] == "BID-" + uuid.UUID(bid["public_id"]).hex.upper()
    assert Decimal(order["total_amount"]) == Decimal("760.00")  # 40 kg x 19.00 (the bid, not the listing's 20.00)
    assert order["delivery_address_snapshot"]["city"] == "Pune"
    assert await _available(a["listing"]) == Decimal("60")
    assert await _bid_statuses(a["event"]) == {bid["public_id"]: "WON", rival_bid["public_id"]: "LOST"}

    # The buyer sees the order; the event (now closed) shows the winner to its farmer.
    assert (await client.get(f"/api/v2/orders/{order['public_id']}", headers=_auth(a["buyer"], make_token))).status_code == 200
    event = (await client.get(f"{EVENTS}/{a['event']}", headers=_auth(a["farmer"], make_token))).json()
    assert event["winner_bid_id"] == bid["public_id"]


async def test_bid_without_quantity_buys_everything_available(client, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "18.00")).json()
    response = await _accept(client, make_token, a["farmer"], bid["public_id"])
    assert response.status_code == 200, response.text
    assert Decimal(response.json()["order"]["total_amount"]) == Decimal("1800.00")  # 100 kg x 18.00
    assert await _available(a["listing"]) == Decimal("0")


async def test_only_the_event_farmer_can_accept(client, make_user, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "19.00")).json()
    other_farmer = await make_user("FARMER")
    for intruder in (a["buyer"], a["rival"], other_farmer):
        assert (await _accept(client, make_token, intruder, bid["public_id"])).status_code == 404
    assert (await _accept(client, make_token, a["farmer"], str(uuid.uuid4()))).status_code == 404
    assert await _order_count() == 0


async def test_same_bid_accepted_twice_returns_the_same_order(client, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "19.00", quantity="5")).json()
    first = await _accept(client, make_token, a["farmer"], bid["public_id"], key="accept-1")
    again = await _accept(client, make_token, a["farmer"], bid["public_id"], key="accept-1")

    assert first.status_code == again.status_code == 200
    assert again.json()["order"]["public_id"] == first.json()["order"]["public_id"]
    assert again.json()["bid_event"]["winner_bid_id"] == bid["public_id"]
    assert await _order_count() == 1
    assert await _available(a["listing"]) == Decimal("95")


async def test_two_accepts_at_the_same_time_make_one_winner(client, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "19.00", quantity="5")).json()
    rival_bid = (await _bid(client, make_token, a["rival"], a["event"], "19.50", quantity="5")).json()

    responses = await asyncio.gather(
        _accept(client, make_token, a["farmer"], bid["public_id"]),
        _accept(client, make_token, a["farmer"], rival_bid["public_id"]),
    )

    assert sorted(r.status_code for r in responses) == [200, 409]
    assert await _order_count() == 1
    assert await _available(a["listing"]) == Decimal("95")
    assert sorted((await _bid_statuses(a["event"])).values()) == ["LOST", "WON"]


async def test_same_bid_accepted_twice_at_the_same_time_makes_one_order(client, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "19.00", quantity="5")).json()

    responses = await asyncio.gather(*(
        _accept(client, make_token, a["farmer"], bid["public_id"], key="voice-yes") for _ in range(2)
    ))

    assert [r.status_code for r in responses] == [200, 200]
    assert responses[0].json()["order"]["public_id"] == responses[1].json()["order"]["public_id"]
    assert await _order_count() == 1


async def test_no_bids_after_a_winner_is_chosen(client, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "19.00", quantity="5")).json()
    assert (await _accept(client, make_token, a["farmer"], bid["public_id"])).status_code == 200
    # Closed events are hidden from other buyers (404), and the loser's bid can't be accepted.
    assert (await _bid(client, make_token, a["rival"], a["event"], "30.00")).status_code == 404


async def test_accept_needs_the_buyers_delivery_address(client, make_user, make_token, auction):
    a = auction
    homeless = await make_user("BUYER")
    bid = (await _bid(client, make_token, homeless, a["event"], "19.00")).json()
    response = await _accept(client, make_token, a["farmer"], bid["public_id"])
    assert response.status_code == 409
    assert await _order_count() == 0
    # Nothing changed: the event is still open.
    event = (await client.get(f"{EVENTS}/{a['event']}", headers=_auth(a["farmer"], make_token))).json()
    assert event["status"] == "ACTIVE" and event["winner_bid_id"] is None


async def test_closed_event_can_no_longer_be_changed(client, make_token, auction):
    a = auction
    bid = (await _bid(client, make_token, a["buyer"], a["event"], "19.00", quantity="5")).json()
    assert (await _accept(client, make_token, a["farmer"], bid["public_id"])).status_code == 200
    headers = _auth(a["farmer"], make_token)
    assert (await client.patch(f"{EVENTS}/{a['event']}", json={"starting_price": "1.00"}, headers=headers)).status_code == 409
    assert (await client.delete(f"{EVENTS}/{a['event']}", headers=headers)).status_code == 409
