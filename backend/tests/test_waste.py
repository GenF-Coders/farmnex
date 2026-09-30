"""F1 + F2 for waste_record and waste_utilization_listing (S13).

User A creates a row; user B must get 404 on it (or not see it); the wrong role gets 403; fields the
server owns (recorded_by, seller, status) are ignored when the client sends them.
These tests need a database (TEST_DATABASE_URL); without one they are skipped.
"""

from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.anyio

RECORDS = "/api/v2/waste-records"
LISTINGS = "/api/v2/waste-utilization-listings"


def _auth(user, make_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user)}"}


async def _seed_farm(user, *, with_batch: bool = False) -> dict:
    """Insert a farm (and optionally a farm crop + crop batch) owned by `user`. Returns public ids."""
    from app.core.database import AsyncSessionLocal
    from app.models.crop_batch import CropBatch
    from app.models.crop_type import CropType
    from app.models.farm import Farm
    from app.models.farm_crop import FarmCrop

    async with AsyncSessionLocal() as session:
        farm = Farm(
            user_id=user.id,
            farm_name="Test farm",
            address_line_1="Road 1",
            state="Maharashtra",
            postal_code="411001",
        )
        session.add(farm)
        await session.flush()
        ids = {"farm_id": str(farm.public_id)}
        if with_batch:
            crop_type = CropType(name=f"Tomato-{uuid.uuid4().hex[:8]}", default_unit="kg")
            session.add(crop_type)
            await session.flush()
            farm_crop = FarmCrop(farmer_id=user.id, farm_id=farm.id, crop_type_id=crop_type.id)
            session.add(farm_crop)
            await session.flush()
            batch = CropBatch(
                farm_crop_id=farm_crop.id,
                batch_code=f"B-{uuid.uuid4().hex[:8].upper()}",
                quantity=100,
                available_quantity=100,
                unit="kg",
            )
            session.add(batch)
            await session.flush()
            ids["crop_batch_id"] = str(batch.public_id)
        await session.commit()
        return ids


async def _make_record(client, make_token, user, farm_id: str, **extra) -> dict:
    body = {"farm_id": farm_id, "waste_type": "Stalks", "quantity": "40", "unit": "kg", **extra}
    response = await client.post(RECORDS, json=body, headers=_auth(user, make_token))
    assert response.status_code == 201, response.text
    return response.json()


async def _make_listing(client, make_token, user, record_id: str, **extra) -> dict:
    body = {
        "waste_record_id": record_id,
        "title": "Tomato stalks for compost",
        "utilization_type": "COMPOST",
        "quantity": "30",
        "unit": "kg",
        "price": "2.50",
        **extra,
    }
    response = await client.post(LISTINGS, json=body, headers=_auth(user, make_token))
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
async def farmer(make_user):
    """A farmer with a farm."""
    user = await make_user("FARMER")
    ids = await _seed_farm(user)
    return user, ids


# ---------------------------------------------------------------------------
# Waste records
# ---------------------------------------------------------------------------


async def test_record_create_uses_server_fields_and_public_ids(client, make_user, make_token) -> None:
    user = await make_user("FARMER")
    ids = await _seed_farm(user, with_batch=True)
    other = await make_user("FARMER")

    response = await client.post(
        RECORDS,
        json={
            "farm_id": ids["farm_id"],
            "crop_batch_id": ids["crop_batch_id"],
            "waste_type": "Peels",
            "quantity": "12.5",
            "unit": "kg",
            "recorded_by_id": other.id,  # server-owned: ignored
            "status": "CLOSED",  # server-owned: ignored
        },
        headers=_auth(user, make_token),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ACTIVE"
    assert body["farm_id"] == ids["farm_id"]
    assert body["crop_batch_id"] == ids["crop_batch_id"]
    assert "id" not in body and "recorded_by_id" not in body
    # the row belongs to the caller, not to the id that was sent
    assert (await client.get(f"{RECORDS}/{body['public_id']}", headers=_auth(user, make_token))).status_code == 200
    assert (await client.get(f"{RECORDS}/{body['public_id']}", headers=_auth(other, make_token))).status_code == 404


async def test_record_is_private_to_its_owner(client, make_user, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    intruder = await make_user("FARMER")
    headers = _auth(intruder, make_token)
    url = f"{RECORDS}/{record['public_id']}"

    assert (await client.get(url, headers=headers)).status_code == 404
    assert (await client.patch(url, json={"reason": "hacked"}, headers=headers)).status_code == 404
    assert (await client.delete(url, headers=headers)).status_code == 404
    assert (await client.get(RECORDS, headers=headers)).json() == []
    mine = await client.get(url, headers=_auth(owner, make_token))
    assert mine.status_code == 200 and mine.json()["reason"] is None
    assert len((await client.get(RECORDS, headers=_auth(owner, make_token))).json()) == 1


async def test_record_cannot_use_someone_elses_farm_or_batch(client, make_user, make_token, farmer) -> None:
    _, ids = farmer  # someone else's farm
    intruder = await make_user("FARMER")
    own = await _seed_farm(intruder, with_batch=True)
    headers = _auth(intruder, make_token)
    body = {"waste_type": "Stalks", "quantity": "5", "unit": "kg"}

    stolen_farm = await client.post(RECORDS, json={**body, "farm_id": ids["farm_id"]}, headers=headers)
    assert stolen_farm.status_code == 404

    victim = await make_user("FARMER")
    victim_ids = await _seed_farm(victim, with_batch=True)
    stolen_batch = await client.post(
        RECORDS,
        json={**body, "farm_id": own["farm_id"], "crop_batch_id": victim_ids["crop_batch_id"]},
        headers=headers,
    )
    assert stolen_batch.status_code == 404

    # your own batch, but on a different farm of yours, is also refused
    second_farm = await _seed_farm(intruder)
    wrong_farm = await client.post(
        RECORDS,
        json={**body, "farm_id": second_farm["farm_id"], "crop_batch_id": own["crop_batch_id"]},
        headers=headers,
    )
    assert wrong_farm.status_code == 404


async def test_record_update_cannot_change_owner_farm_or_status(client, make_token, make_user, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    other_farm = await _seed_farm(owner)
    url = f"{RECORDS}/{record['public_id']}"

    response = await client.patch(
        url,
        json={
            "reason": "spoiled",
            "farm_id": other_farm["farm_id"],  # not updatable: ignored
            "status": "CLOSED",  # not updatable: ignored
            "recorded_by_id": 999999,  # not updatable: ignored
        },
        headers=_auth(owner, make_token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reason"] == "spoiled"
    assert body["farm_id"] == ids["farm_id"]
    assert body["status"] == "ACTIVE"


async def test_only_farmers_can_create_records(client, make_user, make_token, farmer) -> None:
    _, ids = farmer
    buyer = await make_user("BUYER")

    response = await client.post(
        RECORDS,
        json={"farm_id": ids["farm_id"], "waste_type": "Stalks", "quantity": "5", "unit": "kg"},
        headers=_auth(buyer, make_token),
    )

    assert response.status_code == 403


async def test_record_with_listings_cannot_be_deleted(client, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    listing = await _make_listing(client, make_token, owner, record["public_id"])
    headers = _auth(owner, make_token)

    assert (await client.delete(f"{RECORDS}/{record['public_id']}", headers=headers)).status_code == 409
    assert (await client.delete(f"{LISTINGS}/{listing['public_id']}", headers=headers)).status_code == 204
    assert (await client.delete(f"{RECORDS}/{record['public_id']}", headers=headers)).status_code == 204


# ---------------------------------------------------------------------------
# Waste utilization listings
# ---------------------------------------------------------------------------


async def test_listing_create_uses_server_fields(client, make_user, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    other = await make_user("FARMER")

    response = await client.post(
        LISTINGS,
        json={
            "waste_record_id": record["public_id"],
            "title": "Stalks",
            "utilization_type": "COMPOST",
            "quantity": "10",
            "unit": "kg",
            "price": "1",
            "seller_id": other.id,  # server-owned: ignored
            "status": "CLOSED",  # server-owned at creation: ignored
        },
        headers=_auth(owner, make_token),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ACTIVE"
    assert body["seller_id"] == str(owner.public_id)
    assert body["waste_record_id"] == record["public_id"]
    assert "id" not in body


async def test_listing_needs_own_record_and_matching_quantity(client, make_user, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"], quantity="40")
    intruder = await make_user("FARMER")
    body = {
        "waste_record_id": record["public_id"],
        "title": "Stalks",
        "utilization_type": "COMPOST",
        "quantity": "10",
        "unit": "kg",
        "price": "1",
    }

    stolen = await client.post(LISTINGS, json=body, headers=_auth(intruder, make_token))
    assert stolen.status_code == 404

    too_much = await client.post(LISTINGS, json={**body, "quantity": "41"}, headers=_auth(owner, make_token))
    assert too_much.status_code == 422


async def test_only_farmers_can_create_listings(client, make_user, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    buyer = await make_user("BUYER")

    response = await client.post(
        LISTINGS,
        json={
            "waste_record_id": record["public_id"],
            "title": "Stalks",
            "utilization_type": "COMPOST",
            "quantity": "10",
            "unit": "kg",
            "price": "1",
        },
        headers=_auth(buyer, make_token),
    )

    assert response.status_code == 403


async def test_active_listing_is_public_but_only_the_seller_changes_it(client, make_user, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    listing = await _make_listing(client, make_token, owner, record["public_id"])
    buyer = await make_user("BUYER")
    headers = _auth(buyer, make_token)
    url = f"{LISTINGS}/{listing['public_id']}"

    assert (await client.get(url, headers=headers)).status_code == 200
    assert [x["public_id"] for x in (await client.get(LISTINGS, headers=headers)).json()] == [listing["public_id"]]
    assert (await client.patch(url, json={"price": "0"}, headers=headers)).status_code == 404
    assert (await client.delete(url, headers=headers)).status_code == 404
    still = await client.get(url, headers=_auth(owner, make_token))
    assert float(still.json()["price"]) == 2.5


async def test_closed_listing_is_hidden_from_others(client, make_user, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    listing = await _make_listing(client, make_token, owner, record["public_id"])
    url = f"{LISTINGS}/{listing['public_id']}"
    owner_headers = _auth(owner, make_token)
    buyer_headers = _auth(await make_user("BUYER"), make_token)

    closed = await client.patch(url, json={"status": "CLOSED"}, headers=owner_headers)
    assert closed.status_code == 200 and closed.json()["status"] == "CLOSED"

    assert (await client.get(url, headers=buyer_headers)).status_code == 404
    assert (await client.get(LISTINGS, headers=buyer_headers)).json() == []
    assert (await client.get(url, headers=owner_headers)).status_code == 200
    assert len((await client.get(LISTINGS, params={"mine": "true"}, headers=owner_headers)).json()) == 1


async def test_listing_update_cannot_change_seller_or_record(client, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"])
    other_record = await _make_record(client, make_token, owner, ids["farm_id"])
    listing = await _make_listing(client, make_token, owner, record["public_id"])

    response = await client.patch(
        f"{LISTINGS}/{listing['public_id']}",
        json={
            "title": "New title",
            "waste_record_id": other_record["public_id"],  # not updatable: ignored
            "seller_id": 999999,  # not updatable: ignored
        },
        headers=_auth(owner, make_token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "New title"
    assert body["waste_record_id"] == record["public_id"]
    assert body["seller_id"] == str(owner.public_id)


async def test_listing_stays_consistent_with_its_record(client, make_token, farmer) -> None:
    owner, ids = farmer
    record = await _make_record(client, make_token, owner, ids["farm_id"], quantity="40")
    listing = await _make_listing(client, make_token, owner, record["public_id"], quantity="30")
    headers = _auth(owner, make_token)

    wrong_unit = await client.post(
        LISTINGS,
        json={
            "waste_record_id": record["public_id"],
            "title": "t",
            "utilization_type": "COMPOST",
            "quantity": "5",
            "unit": "tonne",
            "price": "1",
        },
        headers=headers,
    )
    assert wrong_unit.status_code == 422
    assert (await client.patch(f"{LISTINGS}/{listing['public_id']}", json={"quantity": "41"}, headers=headers)).status_code == 422
    assert (await client.patch(f"{RECORDS}/{record['public_id']}", json={"quantity": "10"}, headers=headers)).status_code == 409
    assert (await client.patch(f"{RECORDS}/{record['public_id']}", json={"quantity": "35"}, headers=headers)).status_code == 200
