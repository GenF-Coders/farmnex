"""F12c demo wallet (S20): wallet_ledger, Pay (demo), 20% bid advance, release on delivery, expiry.

Rules (FIX_PLAN F12 prototype minimum items 3-5 + STATUS decisions; Atharv, S20 plan):
- Accepting a bid holds 20% of the order from the buyer, once per bid (however often accept runs).
- `POST /payments/orders/{id}/pay-demo`: only the order's buyer (others 404); the server works out
  the amount (total minus what is held); paying again returns the same payment, never a second HOLD.
- `release_for_order` (S26, on delivery): everything held goes to the farmer, once; not delivered
  -> refused ("early release").
- An unpaid PLACED order older than 30 minutes is cancelled (stock back); a paid one - or a bid order
  with its 20% advance - never. Money held on a cancelled order goes back to the buyer.
The first tests need no database; the rest need TEST_DATABASE_URL.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

import app.main as main_module

pytestmark = pytest.mark.anyio

ORDERS = "/api/v2/orders"
PAYMENTS = "/api/v2/payments"


def _auth(user, make_token, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {make_token(user)}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


# ---------------------------------------------------------------------------
# No database: routes, table and the expiry rule
# ---------------------------------------------------------------------------


def test_pay_demo_route_takes_no_body():
    operation = main_module.app.openapi()["paths"]["/api/v2/payments/orders/{order_id}/pay-demo"]["post"]
    assert "Idempotency-Key" in {p["name"] for p in operation.get("parameters", [])}
    assert "requestBody" not in operation  # no amount, status or payer from the client


def test_wallet_route_is_read_only():
    assert set(main_module.app.openapi()["paths"]["/api/v2/payments/wallet"]) == {"get"}


def test_ledger_table_is_registered_with_a_unique_key():
    from app.core.base import Base

    table = Base.metadata.tables["wallet_ledger"]
    assert table.c.idempotency_key.unique
    assert not table.foreign_keys  # public ids only: nothing existing changes


def test_expiry_rule():
    from app.services.wallet_service import EXPIRY_STARTS_AT, _is_expired

    now = EXPIRY_STARTS_AT + timedelta(days=1)
    order = lambda status, minutes, number="CHK-1-1": SimpleNamespace(  # noqa: E731
        status=status, placed_at=now - timedelta(minutes=minutes), created_at=now, order_number=number
    )
    assert _is_expired(order("PLACED", 31), now)
    assert not _is_expired(order("PLACED", 29), now)
    assert not _is_expired(order("CONFIRMED", 60), now)
    assert not _is_expired(order("PLACED", 60, "BID-ABC"), now)  # bid orders never expire
    assert not _is_expired(order("PLACED", 60 * 24 * 2), now)  # placed before S20: left alone


@pytest.fixture(autouse=True)
def _expiry_from_long_ago(monkeypatch):
    """The DB tests place orders 'N minutes ago'; let the expiry start well before that."""
    import app.services.wallet_service as wallet_service

    monkeypatch.setattr(wallet_service, "EXPIRY_STARTS_AT", datetime(2000, 1, 1, tzinfo=timezone.utc))


async def test_wallet_and_pay_need_login(client):
    assert (await client.get(f"{PAYMENTS}/wallet")).status_code == 401
    assert (await client.post(f"{PAYMENTS}/orders/{uuid.uuid4()}/pay-demo")).status_code == 401


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


async def _seed_listing(farmer, *, listing_type="FIXED_PRICE", price="25.00", quantity="100") -> uuid.UUID:
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
            seller_id=farmer.id, farm_id=farm.id, crop_batch_id=batch.id, title="Tomatoes",
            listing_type=listing_type, price=Decimal(price), quantity=Decimal(quantity),
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


async def _ledger(order_id) -> list[tuple[str, Decimal]]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.wallet_ledger import WalletLedgerEntry

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(WalletLedgerEntry.entry_type, WalletLedgerEntry.amount)
            .where(WalletLedgerEntry.order_public_id == uuid.UUID(str(order_id)))
            .order_by(WalletLedgerEntry.id)
        )
        return [(entry_type, amount) for entry_type, amount in result.all()]


async def _order_status(order_id) -> str:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.order import Order

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Order.status).where(Order.public_id == uuid.UUID(str(order_id))))
        return result.scalar_one()


async def _set_order(order_id, **values) -> None:
    """Test-only shortcut for what other steps do (S26 sets DELIVERED; time passing for expiry)."""
    from sqlalchemy import update

    from app.core.database import AsyncSessionLocal
    from app.models.order import Order

    async with AsyncSessionLocal() as session:
        await session.execute(update(Order).where(Order.public_id == uuid.UUID(str(order_id))).values(**values))
        await session.commit()


async def _delete_ledger(order_id) -> None:
    """Test DB only: make an order look like it was made before the wallet existed."""
    from sqlalchemy import delete

    from app.core.database import AsyncSessionLocal
    from app.models.wallet_ledger import WalletLedgerEntry

    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(WalletLedgerEntry).where(WalletLedgerEntry.order_public_id == uuid.UUID(str(order_id)))
        )
        await session.commit()


async def _payment_statuses(order_id) -> list[str]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.models.order import Order
    from app.models.payment import Payment

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Payment.status).join(Order, Order.id == Payment.order_id)
            .where(Order.public_id == uuid.UUID(str(order_id))).order_by(Payment.id)
        )
        return list(result.scalars().all())


def _ago(minutes: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes)


async def _checkout(client, make_token, buyer, listing_id, quantity="4") -> dict:
    response = await client.post(
        ORDERS, json={"items": [{"listing_id": str(listing_id), "quantity": quantity}]},
        headers=_auth(buyer, make_token),
    )
    assert response.status_code == 201, response.text
    return response.json()["orders"][0]


async def _pay(client, make_token, user, order_id, key: str | None = None, **kwargs):
    return await client.post(f"{PAYMENTS}/orders/{order_id}/pay-demo", headers=_auth(user, make_token, key), **kwargs)


@pytest.fixture
async def shop(client, make_user, make_token):
    """A farmer's 100 kg at 25.00/kg and a buyer with a default address who ordered 4 kg (100.00)."""
    farmer, buyer, other = await make_user("FARMER"), await make_user("BUYER"), await make_user("BUYER")
    await _seed_address(buyer)
    listing = await _seed_listing(farmer)
    order = await _checkout(client, make_token, buyer, listing)
    return {"farmer": farmer, "buyer": buyer, "other": other, "listing": listing, "order": order["public_id"]}


@pytest.fixture
async def won_bid(client, make_user, make_token):
    """A pre-bid event; the farmer accepts the buyer's bid of 20.00/kg x 10 kg (order total 200.00)."""
    farmer, buyer = await make_user("FARMER"), await make_user("BUYER")
    await _seed_address(buyer)
    listing = await _seed_listing(farmer, listing_type="PRE_BID", price="20.00")
    now = datetime.now(timezone.utc)
    event = await client.post(
        "/api/v2/bid-events",
        json={"listing_id": str(listing), "starts_at": (now - timedelta(hours=1)).isoformat(),
              "ends_at": (now + timedelta(days=7)).isoformat(), "starting_price": "18.00",
              "minimum_increment": "0.50"},
        headers=_auth(farmer, make_token),
    )
    assert event.status_code == 201, event.text
    bid = await client.post("/api/v2/bids", json={"bid_event_id": event.json()["public_id"], "amount": "20.00",
                                                   "quantity": "10"}, headers=_auth(buyer, make_token))
    assert bid.status_code == 201, bid.text
    bid_id = bid.json()["public_id"]
    accepted = await client.post(f"/api/v2/bids/{bid_id}/accept", headers=_auth(farmer, make_token, "accept-1"))
    assert accepted.status_code == 200, accepted.text
    return {"farmer": farmer, "buyer": buyer, "bid": bid_id, "order": accepted.json()["order"]["public_id"]}


# ---------------------------------------------------------------------------
# Pay (demo)
# ---------------------------------------------------------------------------


async def test_buyer_pays_the_server_amount(client, make_token, shop):
    # Anything the client sends in a body is ignored: the amount comes from the order.
    response = await _pay(client, make_token, shop["buyer"], shop["order"], json={"amount": "1", "status": "RELEASED"})

    assert response.status_code == 200, response.text
    payment = response.json()
    assert Decimal(payment["amount"]) == Decimal("100.00")
    assert payment["status"] == "HELD" and payment["provider"] == "DEMO" and payment["paid_at"]
    assert payment["order_id"] == shop["order"]
    assert await _ledger(shop["order"]) == [("HOLD", Decimal("100.00"))]


async def test_paying_twice_holds_once(client, make_token, shop):
    first = await _pay(client, make_token, shop["buyer"], shop["order"], "pay-1")
    again = await _pay(client, make_token, shop["buyer"], shop["order"], "pay-2")
    assert first.status_code == again.status_code == 200
    assert first.json()["public_id"] == again.json()["public_id"]
    assert await _ledger(shop["order"]) == [("HOLD", Decimal("100.00"))]


async def test_two_pays_at_the_same_time_hold_once(client, make_token, shop):
    responses = await asyncio.gather(*[_pay(client, make_token, shop["buyer"], shop["order"]) for _ in range(3)])
    assert {r.status_code for r in responses} == {200}
    assert len({r.json()["public_id"] for r in responses}) == 1
    assert await _ledger(shop["order"]) == [("HOLD", Decimal("100.00"))]


@pytest.mark.parametrize("who", ["farmer", "other"])
async def test_only_the_buyer_can_pay(client, make_token, shop, who):
    response = await _pay(client, make_token, shop[who], shop["order"])
    assert response.status_code == 404
    assert await _ledger(shop["order"]) == []


async def test_cancelled_order_cannot_be_paid(client, make_token, shop):
    cancel = await client.patch(f"{ORDERS}/{shop['order']}", json={"status": "CANCELLED"},
                                headers=_auth(shop["buyer"], make_token))
    assert cancel.status_code == 200, cancel.text
    assert (await _pay(client, make_token, shop["buyer"], shop["order"])).status_code == 409


async def test_expired_order_cannot_be_paid(client, make_token, shop):
    await _set_order(shop["order"], placed_at=_ago(31))
    assert (await _pay(client, make_token, shop["buyer"], shop["order"])).status_code == 409
    assert await _ledger(shop["order"]) == []


async def test_wallet_shows_money_on_both_sides(client, make_token, shop):
    await _pay(client, make_token, shop["buyer"], shop["order"])

    buyer = (await client.get(f"{PAYMENTS}/wallet", headers=_auth(shop["buyer"], make_token))).json()
    assert Decimal(buyer["held_from_me"]) == Decimal("100.00") and Decimal(buyer["held_for_me"]) == 0
    assert [(e["entry_type"], e["order_id"]) for e in buyer["entries"]] == [("HOLD", shop["order"])]

    farmer = (await client.get(f"{PAYMENTS}/wallet", headers=_auth(shop["farmer"], make_token))).json()
    assert Decimal(farmer["held_for_me"]) == Decimal("100.00") and Decimal(farmer["received"]) == 0
    assert farmer["entries"] == []

    other = (await client.get(f"{PAYMENTS}/wallet", headers=_auth(shop["other"], make_token))).json()
    assert Decimal(other["held_from_me"]) == Decimal(other["held_for_me"]) == 0 and other["entries"] == []


# ---------------------------------------------------------------------------
# Bid advance (20%)
# ---------------------------------------------------------------------------


async def test_accepting_a_bid_holds_20_percent_once(client, make_token, won_bid):
    assert await _ledger(won_bid["order"]) == [("HOLD", Decimal("40.00"))]  # 20% of 200.00

    again = await client.post(f"/api/v2/bids/{won_bid['bid']}/accept",
                              headers=_auth(won_bid["farmer"], make_token, "accept-2"))
    assert again.status_code == 200
    assert await _ledger(won_bid["order"]) == [("HOLD", Decimal("40.00"))]

    payments = (await client.get(PAYMENTS, headers=_auth(won_bid["buyer"], make_token))).json()
    assert [(p["payment_method"], p["status"], Decimal(p["amount"])) for p in payments] == [
        ("BID_ADVANCE_20", "HELD", Decimal("40.00"))
    ]


async def test_buyer_pays_the_rest_after_the_advance(client, make_token, won_bid):
    response = await _pay(client, make_token, won_bid["buyer"], won_bid["order"])
    assert response.status_code == 200
    assert Decimal(response.json()["amount"]) == Decimal("160.00")
    assert await _ledger(won_bid["order"]) == [("HOLD", Decimal("40.00")), ("HOLD", Decimal("160.00"))]


# ---------------------------------------------------------------------------
# Release on delivery (S26 calls release_for_order)
# ---------------------------------------------------------------------------


async def test_no_release_before_delivery(client, make_token, shop):
    from app.core.exceptions import ConflictError
    from app.services.wallet_service import release_for_order

    await _pay(client, make_token, shop["buyer"], shop["order"])
    with pytest.raises(ConflictError):
        await release_for_order(uuid.UUID(shop["order"]))
    assert await _ledger(shop["order"]) == [("HOLD", Decimal("100.00"))]


async def test_release_on_delivery_happens_once(client, make_token, won_bid):
    from app.services.wallet_service import release_for_order

    await _pay(client, make_token, won_bid["buyer"], won_bid["order"])
    await _set_order(won_bid["order"], status="DELIVERED")

    results = await asyncio.gather(*[release_for_order(uuid.UUID(won_bid["order"])) for _ in range(3)])

    assert sorted(results, key=str) == [Decimal("200.00"), None, None]
    assert await _ledger(won_bid["order"]) == [
        ("HOLD", Decimal("40.00")), ("HOLD", Decimal("160.00")), ("RELEASE", Decimal("200.00"))
    ]
    assert await _payment_statuses(won_bid["order"]) == ["RELEASED", "RELEASED"]
    farmer = (await client.get(f"{PAYMENTS}/wallet", headers=_auth(won_bid["farmer"], make_token))).json()
    assert Decimal(farmer["received"]) == Decimal("200.00") and Decimal(farmer["held_for_me"]) == 0
    buyer = (await client.get(f"{PAYMENTS}/wallet", headers=_auth(won_bid["buyer"], make_token))).json()
    assert Decimal(buyer["held_from_me"]) == 0


# ---------------------------------------------------------------------------
# 30-minute expiry and refunds (the timer runs run_wallet_jobs every 5 minutes)
# ---------------------------------------------------------------------------


async def test_unpaid_order_expires_after_30_minutes(client, make_token, shop):
    from app.services.wallet_service import run_wallet_jobs

    assert await _available(shop["listing"]) == Decimal("96")
    await run_wallet_jobs()
    assert await _order_status(shop["order"]) == "PLACED"  # still young

    await _set_order(shop["order"], placed_at=_ago(31))
    assert await run_wallet_jobs() == (1, 0)
    assert await _order_status(shop["order"]) == "CANCELLED"
    assert await _available(shop["listing"]) == Decimal("100")  # stock back, through S18's cancel
    assert await run_wallet_jobs() == (0, 0)  # nothing twice
    assert await _available(shop["listing"]) == Decimal("100")


async def test_paid_order_never_expires(client, make_token, shop):
    from app.services.wallet_service import run_wallet_jobs

    await _pay(client, make_token, shop["buyer"], shop["order"])
    await _set_order(shop["order"], placed_at=_ago(120))
    assert await run_wallet_jobs() == (0, 0)
    assert await _order_status(shop["order"]) == "PLACED"


async def test_bid_order_with_advance_never_expires(client, make_token, won_bid):
    from app.services.wallet_service import run_wallet_jobs

    await _set_order(won_bid["order"], placed_at=_ago(120))
    assert await run_wallet_jobs() == (0, 0)
    assert await _order_status(won_bid["order"]) == "PLACED"


async def test_orders_from_before_s20_are_left_alone(client, make_token, shop, won_bid, monkeypatch):
    """The first timer run after the deploy must not cancel rows already in the live database:
    orders placed before EXPIRY_STARTS_AT, and bid orders from S19 that have no advance."""
    import app.services.wallet_service as wallet_service
    from app.services.wallet_service import run_wallet_jobs

    await _set_order(shop["order"], placed_at=_ago(120))
    monkeypatch.setattr(wallet_service, "EXPIRY_STARTS_AT", datetime.now(timezone.utc) - timedelta(minutes=60))
    assert await run_wallet_jobs() == (0, 0)  # placed before the start
    assert await _order_status(shop["order"]) == "PLACED"

    await _delete_ledger(won_bid["order"])  # like an S19 order: accepted before the wallet existed
    await _set_order(won_bid["order"], placed_at=_ago(40))
    assert await run_wallet_jobs() == (0, 0)
    assert await _order_status(won_bid["order"]) == "PLACED"


async def test_pay_and_expiry_at_the_same_time_leave_one_winner(client, make_token, shop):
    """Just before the cut-off the buyer pays while the timer runs 'after' it: either the payment or
    the expiry wins, never both (a cancelled order with money held, or a paid order without stock)."""
    from app.services.wallet_service import run_wallet_jobs

    await _set_order(shop["order"], placed_at=_ago(29))
    later = datetime.now(timezone.utc) + timedelta(minutes=5)
    pay, _ = await asyncio.gather(_pay(client, make_token, shop["buyer"], shop["order"]), run_wallet_jobs(later))

    status, ledger = await _order_status(shop["order"]), await _ledger(shop["order"])
    if pay.status_code == 200:
        assert status == "PLACED" and ledger == [("HOLD", Decimal("100.00"))]
    else:
        assert pay.status_code == 409 and status == "CANCELLED" and ledger == []
        assert await _available(shop["listing"]) == Decimal("100")


async def test_money_on_a_cancelled_order_goes_back(client, make_token, shop):
    from app.services.wallet_service import run_wallet_jobs

    await _pay(client, make_token, shop["buyer"], shop["order"])
    cancel = await client.patch(f"{ORDERS}/{shop['order']}", json={"status": "CANCELLED"},
                                headers=_auth(shop["buyer"], make_token))
    assert cancel.status_code == 200

    assert await run_wallet_jobs() == (0, 1)
    assert await run_wallet_jobs() == (0, 0)
    assert await _ledger(shop["order"]) == [("HOLD", Decimal("100.00")), ("REFUND", Decimal("100.00"))]
    assert await _payment_statuses(shop["order"]) == ["REFUNDED"]
    buyer = (await client.get(f"{PAYMENTS}/wallet", headers=_auth(shop["buyer"], make_token))).json()
    assert Decimal(buyer["refunded"]) == Decimal("100.00") and Decimal(buyer["held_from_me"]) == 0
