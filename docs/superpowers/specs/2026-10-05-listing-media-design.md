# Lot photos/videos + "Verified by FarmNex" badge — design (2026-10-05)

Agreed with Atharv in chat on 2026-10-05.

## Goal
A farmer adds camera photos and short videos to a lot they listed, so buyers can see the produce with
their own eyes, and a FarmNex admin can check it and give the lot a **✅ Verified** badge.

## Decisions
- **Camera only** (phone camera opens directly; in a laptop browser the browser shows a file chooser —
  browsers can't force the camera).
- **Short videos:** max 15 s recording, max **10 MB** per file (the existing upload limit is kept).
- **Limits:** 6 photos + 2 videos per lot.
- **Re-verify:** adding or deleting media removes the badge; the lot goes back to "waiting for review".
- **Admin reject** needs a short reason, which the farmer sees.
- The old Pre-bid photo box (kept files only on the phone) is replaced by the real one (view only there;
  farmers add media from My crops). The Crop Rescue buyer view is unchanged (its lots aren't listings).

## Data (new tables only, prefix `lv_`)
- `lv_listing_media`: one row per photo/video — listing, uploader, kind (PHOTO/VIDEO), storage path,
  content type, size, created_at.
- `lv_listing_verifications`: one row per listing that has media — status PENDING / VERIFIED / REJECTED,
  reason, reviewer, reviewed_at.
Created by `create_all` at startup; `backend/migrations/050_lv_listing_media.sql` creates them too and
turns on row-level security (run by hand in Supabase).

## API (all need login)
| Call | Who | Rule |
|---|---|---|
| `POST /api/v2/product-listings/{id}/media` (file) | the listing's seller | listing not closed; JPG/PNG/WebP photo or MP4/MOV video, real file signature checked, ≤ 10 MB, within limits; resets status to PENDING |
| `GET /api/v2/product-listings/{id}/media` | anyone who can see the listing | items with 15-minute signed links + verification status |
| `DELETE /api/v2/product-listings/{id}/media/{media_id}` | the listing's seller | removes row + file; PENDING again (or no status if no media left) |
| `GET /api/v2/admin/listing-verifications?status=PENDING` | ADMIN, SUPER_ADMIN | lots waiting for review |
| `POST /api/v2/admin/listing-verifications/{id}` `{decision, reason, reviewed_media_ids}` | ADMIN, SUPER_ADMIN | VERIFIED or REJECTED (reason required); 409 if the media changed since the admin looked |

Listing responses gain optional `verification_status` and `media_count` (for the Market badge).
Not your listing → 404. Files live in the private bucket under `listing-media/`.

## App
- My crops: each lot gets **📷 Photos & video** → sheet with camera buttons, thumbnails, delete, status.
- Market card: **✅ Verified** tag. Lot details (pre-bid dialog): photos, video player, badge.
- Admin: **Verify lots** screen with Verify / Reject.

## Safety
No existing table, column or row changes. Storage service only gains the `listing-media` folder; its
existing checks are unchanged. Tests cover owner/other-farmer/buyer/admin rules.
