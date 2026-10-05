"""Lot photos/videos + "Verified by FarmNex" (docs/superpowers/specs/2026-10-05-listing-media-design.md).

The file checks run without a database. The rest need TEST_DATABASE_URL and skip without it.
File storage is always faked: nothing is sent to Supabase.
"""

from __future__ import annotations

import uuid

import pytest

from app.core.exceptions import ValidationError
from app.services.listing_media_service import ListingMediaService
from app.services.storage_service import StorageService, storage_service

pytestmark = pytest.mark.anyio

LISTINGS = "/api/v2/product-listings"
QUEUE = "/api/v2/admin/listing-verifications"

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 64
PDF = b"%PDF-1.7" + b"\x00" * 64


# --- file checks (no database) ---------------------------------------------------------


def _checker() -> ListingMediaService:
    return ListingMediaService(repository=None, storage=StorageService())  # type: ignore[arg-type]


def test_photos_and_videos_with_real_signatures_are_accepted():
    assert _checker()._check_file(JPEG, "image/jpeg") == ("PHOTO", "image/jpeg", "jpg")
    assert _checker()._check_file(MP4, "video/mp4") == ("VIDEO", "video/mp4", "mp4")
    assert _checker()._check_file(MP4, "video/quicktime")[0] == "VIDEO"


@pytest.mark.parametrize(
    "data, content_type",
    [
        (MP4, "image/jpeg"),  # a video pretending to be a photo
        (JPEG, "video/mp4"),  # a photo pretending to be a video
        (PDF, "application/pdf"),  # not a photo or video at all
        (b"", "image/jpeg"),
    ],
)
def test_wrong_or_fake_files_are_refused(data, content_type):
    with pytest.raises(ValidationError):
        _checker()._check_file(data, content_type)


def test_files_over_the_limit_are_refused(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "storage_max_upload_size_bytes", 50)
    with pytest.raises(ValidationError, match="upload limit"):
        _checker()._check_file(JPEG, "image/jpeg")


# --- with a database -------------------------------------------------------------------


@pytest.fixture
def stored(monkeypatch) -> dict[str, bytes]:
    """Fake file storage: uploads land in this dict, signed links are fake."""
    files: dict[str, bytes] = {}

    async def upload(*, path, file_bytes, **_):
        files[path] = file_bytes

    async def delete(*, path, **_):
        files.pop(path, None)

    async def create_signed_url(*, path, **_):
        return f"https://signed.example/{path}"

    monkeypatch.setattr(storage_service, "upload", upload)
    monkeypatch.setattr(storage_service, "delete", delete)
    monkeypatch.setattr(storage_service, "create_signed_url", create_signed_url)
    return files


def _auth(user, make_token) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(user)}"}


async def _listing(client, make_token, user) -> str:
    """A farm, crop type, farm crop, batch and ACTIVE listing owned by `user`; returns the listing id."""
    from app.core.database import AsyncSessionLocal
    from app.models.crop_type import CropType
    from app.models.farm import Farm
    from app.models.farm_crop import FarmCrop

    async with AsyncSessionLocal() as session:
        farm = Farm(user_id=user.id, farm_name="Test farm", address_line_1="Road 1", state="Maharashtra", postal_code="411001")
        crop_type = CropType(name=f"Tomato-{uuid.uuid4().hex[:8]}", default_unit="kg")
        session.add_all([farm, crop_type])
        await session.flush()
        farm_crop = FarmCrop(farmer_id=user.id, farm_id=farm.id, crop_type_id=crop_type.id)
        session.add(farm_crop)
        await session.commit()
        farm_id, farm_crop_id = str(farm.public_id), str(farm_crop.public_id)

    headers = _auth(user, make_token)
    batch = await client.post("/api/v2/crop-batches", json={"farm_crop_id": farm_crop_id, "quantity": "100", "unit": "kg"}, headers=headers)
    assert batch.status_code == 201, batch.text
    listing = await client.post(
        LISTINGS,
        json={"farm_id": farm_id, "crop_batch_id": batch.json()["public_id"], "title": "Fresh tomatoes",
              "listing_type": "FIXED_PRICE", "price": "25", "quantity": "100", "unit": "kg"},
        headers=headers,
    )
    assert listing.status_code == 201, listing.text
    return listing.json()["public_id"]


async def _upload(client, headers, listing_id, data=JPEG, content_type="image/jpeg"):
    return await client.post(
        f"{LISTINGS}/{listing_id}/media", files={"file": ("lot.bin", data, content_type)}, headers=headers
    )


async def _seen(client, headers, listing_id) -> list[str]:
    """The media ids an admin sees on the lot right now."""
    media = (await client.get(f"{LISTINGS}/{listing_id}/media", headers=headers)).json()
    return [item["public_id"] for item in media["items"]]


async def test_farmer_adds_photo_and_video_and_buyer_sees_them(client, make_user, make_token, stored):
    farmer, buyer = await make_user("FARMER"), await make_user("BUYER")
    listing_id = await _listing(client, make_token, farmer)
    headers = _auth(farmer, make_token)

    photo = await _upload(client, headers, listing_id)
    video = await _upload(client, headers, listing_id, MP4, "video/mp4")
    assert photo.status_code == 201, photo.text
    assert video.status_code == 201, video.text
    assert len(stored) == 2 and all(path.startswith("listing-media/") for path in stored)

    seen = (await client.get(f"{LISTINGS}/{listing_id}/media", headers=_auth(buyer, make_token))).json()
    assert [item["kind"] for item in seen["items"]] == ["PHOTO", "VIDEO"]
    assert seen["items"][0]["url"].startswith("https://signed.example/listing-media/")
    assert "storage_path" not in seen["items"][0] and "id" not in seen["items"][0]
    assert seen["verification"]["status"] == "PENDING"


async def test_only_the_seller_adds_or_deletes(client, make_user, make_token, stored):
    farmer, rival, buyer = await make_user("FARMER"), await make_user("FARMER"), await make_user("BUYER")
    listing_id = await _listing(client, make_token, farmer)
    media_id = (await _upload(client, _auth(farmer, make_token), listing_id)).json()["items"][0]["public_id"]

    assert (await _upload(client, _auth(rival, make_token), listing_id)).status_code == 404
    assert (await _upload(client, _auth(buyer, make_token), listing_id)).status_code == 403
    for user in (rival, buyer):
        response = await client.delete(f"{LISTINGS}/{listing_id}/media/{media_id}", headers=_auth(user, make_token))
        assert response.status_code in (403, 404)
    assert len(stored) == 1


async def test_limits_and_fake_files(client, make_user, make_token, stored):
    farmer = await make_user("FARMER")
    listing_id = await _listing(client, make_token, farmer)
    headers = _auth(farmer, make_token)

    assert (await _upload(client, headers, listing_id, MP4, "image/jpeg")).status_code == 422
    for _ in range(2):
        assert (await _upload(client, headers, listing_id, MP4, "video/mp4")).status_code == 201
    assert (await _upload(client, headers, listing_id, MP4, "video/mp4")).status_code == 409
    for _ in range(6):
        assert (await _upload(client, headers, listing_id)).status_code == 201
    assert (await _upload(client, headers, listing_id)).status_code == 409


async def test_admin_verifies_and_a_change_removes_the_badge(client, make_user, make_token, stored):
    farmer, admin, buyer = await make_user("FARMER"), await make_user("ADMIN"), await make_user("BUYER")
    listing_id = await _listing(client, make_token, farmer)
    farmer_headers, admin_headers = _auth(farmer, make_token), _auth(admin, make_token)
    await _upload(client, farmer_headers, listing_id)

    queue = (await client.get(QUEUE, headers=admin_headers)).json()
    assert [row["listing_id"] for row in queue] == [listing_id]

    seen = await _seen(client, admin_headers, listing_id)
    decided = await client.post(
        f"{QUEUE}/{listing_id}", json={"decision": "VERIFIED", "reviewed_media_ids": seen}, headers=admin_headers
    )
    assert decided.status_code == 200 and decided.json()["verification"]["status"] == "VERIFIED"
    card = (await client.get(f"{LISTINGS}/{listing_id}", headers=_auth(buyer, make_token))).json()
    assert (card["verification_status"], card["media_count"]) == ("VERIFIED", 1)

    # a new photo takes the badge off until FarmNex checks again
    await _upload(client, farmer_headers, listing_id)
    listed = (await client.get(LISTINGS, headers=_auth(buyer, make_token))).json()
    row = next(item for item in listed if item["public_id"] == listing_id)
    assert (row["verification_status"], row["media_count"]) == ("PENDING", 2)


async def test_only_admins_decide_and_rejection_needs_a_reason(client, make_user, make_token, stored):
    farmer, admin = await make_user("FARMER"), await make_user("ADMIN")
    listing_id = await _listing(client, make_token, farmer)
    await _upload(client, _auth(farmer, make_token), listing_id)
    admin_headers = _auth(admin, make_token)

    for user in (farmer, await make_user("BUYER")):
        headers = _auth(user, make_token)
        assert (await client.get(QUEUE, headers=headers)).status_code == 403
        body = {"decision": "VERIFIED", "reviewed_media_ids": [str(uuid.uuid4())]}
        assert (await client.post(f"{QUEUE}/{listing_id}", json=body, headers=headers)).status_code == 403

    seen = await _seen(client, admin_headers, listing_id)
    no_reason = await client.post(
        f"{QUEUE}/{listing_id}", json={"decision": "REJECTED", "reviewed_media_ids": seen}, headers=admin_headers
    )
    assert no_reason.status_code == 422
    rejected = await client.post(
        f"{QUEUE}/{listing_id}",
        json={"decision": "REJECTED", "reason": "Photo is blurry", "reviewed_media_ids": seen},
        headers=admin_headers,
    )
    assert rejected.json()["verification"] == {**rejected.json()["verification"], "status": "REJECTED", "reason": "Photo is blurry"}
    farmer_view = (await client.get(f"{LISTINGS}/{listing_id}/media", headers=_auth(farmer, make_token))).json()
    assert farmer_view["verification"]["reason"] == "Photo is blurry"


async def test_deleting_the_last_photo_clears_the_status(client, make_user, make_token, stored):
    farmer = await make_user("FARMER")
    listing_id = await _listing(client, make_token, farmer)
    headers = _auth(farmer, make_token)
    media_id = (await _upload(client, headers, listing_id)).json()["items"][0]["public_id"]

    after = await client.delete(f"{LISTINGS}/{listing_id}/media/{media_id}", headers=headers)
    assert after.status_code == 200
    assert after.json() | {"listing_id": None} == {
        "listing_id": None, "verification": {"status": "NONE", "reason": None, "reviewed_at": None},
        "items": [], "max_photos": 6, "max_videos": 2,
    }
    assert stored == {}


async def test_closed_listing_hides_media_from_others(client, make_user, make_token, stored):
    farmer, buyer = await make_user("FARMER"), await make_user("BUYER")
    listing_id = await _listing(client, make_token, farmer)
    await _upload(client, _auth(farmer, make_token), listing_id)
    await client.delete(f"{LISTINGS}/{listing_id}", headers=_auth(farmer, make_token))

    assert (await client.get(f"{LISTINGS}/{listing_id}/media", headers=_auth(buyer, make_token))).status_code == 404
    assert (await _upload(client, _auth(farmer, make_token), listing_id)).status_code == 409


async def test_verify_is_refused_if_the_farmer_swapped_photos_meanwhile(client, make_user, make_token, stored):
    farmer, admin = await make_user("FARMER"), await make_user("ADMIN")
    listing_id = await _listing(client, make_token, farmer)
    farmer_headers, admin_headers = _auth(farmer, make_token), _auth(admin, make_token)
    await _upload(client, farmer_headers, listing_id)

    seen = await _seen(client, admin_headers, listing_id)  # the admin looks at the good photo...
    await client.delete(f"{LISTINGS}/{listing_id}/media/{seen[0]}", headers=farmer_headers)  # ...farmer swaps it
    await _upload(client, farmer_headers, listing_id)

    swapped = await client.post(
        f"{QUEUE}/{listing_id}", json={"decision": "VERIFIED", "reviewed_media_ids": seen}, headers=admin_headers
    )
    assert swapped.status_code == 409
    status = (await client.get(f"{LISTINGS}/{listing_id}/media", headers=admin_headers)).json()["verification"]
    assert status["status"] == "PENDING"
