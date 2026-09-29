"""Checks that the shared test setup (conftest.py) itself works. Not tests of app features."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.anyio


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_client_reaches_the_app(client) -> None:
    response = await client.get("/health")

    assert response.status_code == 200


async def test_no_token_is_rejected(client) -> None:
    response = await client.get("/api/v2/users/me")

    assert response.status_code == 401


async def test_made_user_can_use_its_token(client, make_user, make_token) -> None:
    farmer = await make_user("FARMER")

    response = await client.get("/api/v2/users/me", headers=_auth(make_token(farmer)))

    assert response.status_code == 200
    assert response.json()["public_id"] == str(farmer.public_id)


async def test_users_get_the_role_they_were_made_with(make_user) -> None:
    buyer = await make_user("BUYER")
    admin = await make_user("ADMIN")

    assert buyer.role.name == "BUYER"
    assert admin.role.name == "ADMIN"
    assert buyer.public_id != admin.public_id


async def test_unknown_role_is_an_error(make_user) -> None:
    with pytest.raises(ValueError):
        await make_user("NOT_A_ROLE")


# The next two tests use the same phone number: the second only passes if the database was
# emptied between tests.
async def test_database_is_clean_between_tests_a(make_user) -> None:
    await make_user("FARMER", phone_number="+919999900001")


async def test_database_is_clean_between_tests_b(make_user) -> None:
    await make_user("FARMER", phone_number="+919999900001")
