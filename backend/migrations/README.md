# backend/migrations — hand-run SQL for component tables

The core tables (users, farms, listings, orders, ...) are created automatically when the backend
starts (`Base.metadata.create_all` in `app/core/database.py`). **Component** tables (Crop Rescue,
forecaster, route optimizer, voice assistant) are created by the SQL files in this folder, run by
hand in the Supabase SQL editor.

## How the main database was built (2026-09-30)

Atharv's own Supabase project `farmnex` (Mumbai) was built empty-to-ready in this order:
`001_core_schema.sql` → `010_cr_crop_rescue.sql` → `011_cr_demo_seed.sql` →
`012_cr_buyer_pool_invoker.sql`, plus a private Storage bucket named `storage-bucket`.

- `001` is **only for a brand-new, empty database** (it is the exact SQL the backend's start-up
  `create_all` would run, plus row-level-security "locks"). It is the one file here that is not
  safe to run twice. It is a record: the backend still creates any missing core table itself.
- After changing a model, refresh `001` with `python dump_core_schema.py` (see that script).
- Every table has row-level security on with no policies: the public Supabase API can't read
  them; the backend connects as the owner and is unaffected.

## Rules for every file here

1. **Only add.** `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `CREATE OR REPLACE VIEW`,
   `ALTER TABLE <own prefixed table> ENABLE ROW LEVEL SECURITY`. Never `DROP`, `TRUNCATE`, `DELETE`,
   `ALTER` a core table, `GRANT`/`REVOKE`, or `CREATE EXTENSION`.
2. **Prefix everything** with the component's prefix: `cr_` Crop Rescue, `fc_` forecaster,
   `rt_` route optimizer, `va_` voice assistant.
3. **No foreign keys to core tables.** Store users as `user_public_id` (UUID), deliveries as
   `delivery_public_id`, etc.
4. **Safe to run twice**, and wrapped in `BEGIN; ... COMMIT;`.
5. Enable RLS on each new table with **no** policies (the backend connects as the DB owner; the app
   never reads these tables directly).

## Numbering

| Range | Component |
|---|---|
| `010–019` | Crop Rescue (`cr_`) |
| `020–029` | AI forecaster (`fc_`) |
| `030–039` | Route optimizer (`rt_`) |
| `040–049` | Voice assistant (`va_`) |

Name: `<number>_<prefix>_<what>.sql`, e.g. `010_cr_crop_rescue.sql`.

## How to run one (Atharv)

1. Supabase dashboard → your FarmNex project → **SQL Editor** → **New query**.
2. Open the file on GitHub, copy everything, paste, click **Run**.
3. Check in **Table Editor** that the new tables appear. Nothing else should change.
4. Tell the coordinator session (or note in the PR) that it's done; it records it in `docs/STATUS.md`.

Claude Code never runs these against the main database itself.
