"""F1 + F2 for buyer_demand_request, notification and crop_type (S14).

User A creates a row; user B must get 404 on it (or not see it); the wrong role gets 403; fields the
server owns (buyer, status, notification owner) are ignored. These tests need a database
(TEST_DATABASE_URL); without one they are skipped.
"""

from __future__ import annotations

import uuid

import pytest

pytestmark = pytest.mark.anyio

DEMANDS = "/api/v2/buyer-demand-requests"
NOTES = "/api/v2/notifications"
CROPS = "/api/v2/crop-types"


def _auth(user, make_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user)}"}


async def _seed_crop_type(*, active: bool = True) -> str:
    from app.core.database import AsyncSessionLocal
    from app.models.crop_type import CropType

    async with AsyncSessionLocal() as session:
        crop = CropType(name=f"Crop-{uuid.uuid4().hex[:8]}", default_unit="kg", is_active=active)
        session.add(crop)
        await session.commit()
        return str(crop.public_id)


async def _seed_notification(user, title: str = "Hello") -> str:
    """Notifications are created by the server, so the tests insert them directly."""
    from app.core.database import AsyncSessionLocal
    from app.models.notification import Notification

    async with AsyncSessionLocal() as session:
        note = Notification(
            user_id=user.id, title=title, message="msg", notification_type="INFO", is_read=False
        )
        session.add(note)
        await session.commit()
        return str(note.public_id)


async def _make_demand(client, make_token, user, crop_id: str, **extra) -> dict:
    body = {"crop_type_id": crop_id, "title": "Need tomatoes", "quantity": "500", "unit": "kg", **extra}
    response = await client.post(DEMANDS, json=body, headers=_auth(user, make_token))
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Crop types
# ---------------------------------------------------------------------------


async def test_crop_type_read_by_everyone_write_by_admin_only(client, make_user, make_token) -> None:
    admin = await make_user("ADMIN")
    farmer = await make_user("FARMER")
    body = {"name": f"Millet-{uuid.uuid4().hex[:6]}", "default_unit": "kg", "is_active": False}

    for role_user in (farmer, await make_user("BUYER")):
        assert (await client.post(CROPS, json=body, headers=_auth(role_user, make_token))).status_code == 403

    created = await client.post(CROPS, json=body, headers=_auth(admin, make_token))
    assert created.status_code == 201, created.text
    crop = created.json()
    assert crop["is_active"] is True  # server-owned: the client's False is ignored

    url = f"{CROPS}/{crop['public_id']}"
    assert (await client.get(url, headers=_auth(farmer, make_token))).status_code == 200
    assert crop["public_id"] in [c["public_id"] for c in (await client.get(CROPS, headers=_auth(farmer, make_token))).json()]

    assert (await client.patch(url, json={"description": "x"}, headers=_auth(farmer, make_token))).status_code == 403
    assert (await client.delete(url, headers=_auth(farmer, make_token))).status_code == 403
    assert (await client.patch(url, json={"description": "x"}, headers=_auth(admin, make_token))).status_code == 200


async def test_crop_type_delete_retires_it_and_hides_it_from_non_admins(client, make_user, make_token) -> None:
    admin = await make_user("ADMIN")
    buyer = await make_user("BUYER")
    crop_id = await _seed_crop_type()
    url = f"{CROPS}/{crop_id}"

    assert (await client.delete(url, headers=_auth(admin, make_token))).status_code == 204

    assert (await client.get(url, headers=_auth(buyer, make_token))).status_code == 404
    assert crop_id not in [c["public_id"] for c in (await client.get(CROPS, headers=_auth(buyer, make_token))).json()]
    seen_by_admin = await client.get(url, headers=_auth(admin, make_token))
    assert seen_by_admin.status_code == 200 and seen_by_admin.json()["is_active"] is False


async def test_crop_type_name_must_be_unique(client, make_user, make_token) -> None:
    admin = await make_user("ADMIN")
    body = {"name": f"Unique-{uuid.uuid4().hex[:6]}", "default_unit": "kg"}

    assert (await client.post(CROPS, json=body, headers=_auth(admin, make_token))).status_code == 201
    assert (await client.post(CROPS, json=body, headers=_auth(admin, make_token))).status_code == 409


# ---------------------------------------------------------------------------
# Buyer demand requests
# ---------------------------------------------------------------------------


async def test_demand_create_uses_server_fields_and_public_ids(client, make_user, make_token) -> None:
    buyer = await make_user("BUYER")
    other = await make_user("BUYER")
    crop_id = await _seed_crop_type()

    response = await client.post(
        DEMANDS,
        json={
            "crop_type_id": crop_id,
            "title": "Need tomatoes",
            "quantity": "500",
            "unit": "kg",
            "buyer_id": other.id,  # server-owned: ignored
            "status": "CLOSED",  # server-owned: ignored
        },
        headers=_auth(buyer, make_token),
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "ACTIVE"
    assert body["buyer_id"] == str(buyer.public_id)
    assert body["crop_type_id"] == crop_id
    assert "id" not in body


async def test_demand_needs_buyer_role_and_an_active_crop_type(client, make_user, make_token) -> None:
    farmer = await make_user("FARMER")
    buyer = await make_user("BUYER")
    crop_id = await _seed_crop_type()
    body = {"crop_type_id": crop_id, "title": "t", "quantity": "5", "unit": "kg"}

    assert (await client.post(DEMANDS, json=body, headers=_auth(farmer, make_token))).status_code == 403
    retired = await _seed_crop_type(active=False)
    assert (await client.post(DEMANDS, json={**body, "crop_type_id": retired}, headers=_auth(buyer, make_token))).status_code == 404
    unknown = str(uuid.uuid4())
    assert (await client.post(DEMANDS, json={**body, "crop_type_id": unknown}, headers=_auth(buyer, make_token))).status_code == 404


async def test_demand_is_private_to_its_buyer(client, make_user, make_token) -> None:
    buyer = await make_user("BUYER")
    demand = await _make_demand(client, make_token, buyer, await _seed_crop_type())
    intruder = await make_user("BUYER")
    headers = _auth(intruder, make_token)
    url = f"{DEMANDS}/{demand['public_id']}"

    assert (await client.get(url, headers=headers)).status_code == 404
    assert (await client.patch(url, json={"title": "hacked"}, headers=headers)).status_code == 404
    assert (await client.delete(url, headers=headers)).status_code == 404
    assert (await client.get(DEMANDS, headers=headers)).json() == []
    mine = await client.get(url, headers=_auth(buyer, make_token))
    assert mine.status_code == 200 and mine.json()["title"] == "Need tomatoes"


async def test_farmers_see_open_demand_but_cannot_change_it(client, make_user, make_token) -> None:
    buyer = await make_user("BUYER")
    farmer = await make_user("FARMER")
    demand = await _make_demand(client, make_token, buyer, await _seed_crop_type())
    url = f"{DEMANDS}/{demand['public_id']}"
    farmer_headers = _auth(farmer, make_token)

    assert (await client.get(url, headers=farmer_headers)).status_code == 200
    assert [d["public_id"] for d in (await client.get(DEMANDS, headers=farmer_headers)).json()] == [demand["public_id"]]
    assert (await client.patch(url, json={"title": "x"}, headers=farmer_headers)).status_code == 404
    assert (await client.delete(url, headers=farmer_headers)).status_code == 404

    # once the buyer closes it, farmers no longer see it
    closed = await client.patch(url, json={"status": "CLOSED"}, headers=_auth(buyer, make_token))
    assert closed.status_code == 200 and closed.json()["status"] == "CLOSED"
    assert (await client.get(url, headers=farmer_headers)).status_code == 404
    assert (await client.get(DEMANDS, headers=farmer_headers)).json() == []


async def test_demand_update_cannot_change_buyer_or_crop_type(client, make_user, make_token) -> None:
    buyer = await make_user("BUYER")
    crop_id = await _seed_crop_type()
    demand = await _make_demand(client, make_token, buyer, crop_id)

    response = await client.patch(
        f"{DEMANDS}/{demand['public_id']}",
        json={
            "title": "New title",
            "crop_type_id": await _seed_crop_type(),  # not updatable: ignored
            "buyer_id": 999999,  # not updatable: ignored
        },
        headers=_auth(buyer, make_token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"] == "New title"
    assert body["crop_type_id"] == crop_id
    assert body["buyer_id"] == str(buyer.public_id)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


async def test_notification_cannot_be_created_over_http(client, make_user, make_token) -> None:
    user = await make_user("FARMER")

    response = await client.post(
        NOTES,
        json={"user_id": user.id, "title": "t", "message": "m", "notification_type": "X", "is_read": False},
        headers=_auth(user, make_token),
    )

    assert response.status_code == 405


async def test_notification_is_private_to_its_user(client, make_user, make_token) -> None:
    owner = await make_user("FARMER")
    intruder = await make_user("FARMER")
    note_id = await _seed_notification(owner)
    url = f"{NOTES}/{note_id}"
    headers = _auth(intruder, make_token)

    assert (await client.get(url, headers=headers)).status_code == 404
    assert (await client.patch(url, json={"is_read": True}, headers=headers)).status_code == 404
    assert (await client.delete(url, headers=headers)).status_code == 404
    assert (await client.get(NOTES, headers=headers)).json() == []
    mine = await client.get(url, headers=_auth(owner, make_token))
    assert mine.status_code == 200 and mine.json()["is_read"] is False
    assert "user_id" not in mine.json() and "id" not in mine.json()


async def test_owner_marks_notification_read_and_unread(client, make_user, make_token) -> None:
    owner = await make_user("BUYER")
    note_id = await _seed_notification(owner)
    url = f"{NOTES}/{note_id}"
    headers = _auth(owner, make_token)

    read = await client.patch(url, json={"is_read": True, "title": "changed", "user_id": 1}, headers=headers)
    assert read.status_code == 200, read.text
    assert read.json()["is_read"] is True and read.json()["read_at"] is not None
    assert read.json()["title"] == "Hello"  # only is_read can change

    unread = await client.patch(url, json={"is_read": False}, headers=headers)
    assert unread.json()["is_read"] is False and unread.json()["read_at"] is None

    assert (await client.delete(url, headers=headers)).status_code == 204
    assert (await client.get(url, headers=headers)).status_code == 404
