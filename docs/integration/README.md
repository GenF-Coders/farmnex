# Plugging components into the main app — shared contract

Four components are built in their own repos and then plugged into this app:
Crop Rescue, AI forecaster, route optimizer, voice assistant. This file is the set of rules they all
follow here. Each component also has its own guide in this folder.

## The picture

```
Flutter app ──(FarmNex login token)──► main FastAPI backend  /api/v2/...
                                         ├─ core routes (users, farms, listings, orders, ...)
                                         ├─ app/modules/crop_rescue      → /api/v2/rescue/...
                                         ├─ app/modules/route_optimizer  → /api/v2/routes/...
                                         ├─ app/modules/forecast (connector) → /api/v2/forecast/...
                                         │        └──(server key)──► forecaster service (separate)
                                         └─ same Supabase PostgreSQL (new prefixed tables only)
voice assistant service (separate) ──(the user's own FarmNex token)──► /api/v2/...
```

The app only ever talks to **our** backend (plus the voice service for audio). Separate services'
keys live only on the server.

## Rules

1. **Where the code goes:** copied router packages live in `backend/app/modules/<name>/`
   (create `backend/app/modules/__init__.py`). Keep the component's own files unchanged where
   possible so updates can be re-copied; put FarmNex-specific glue in `backend/app/modules/wiring.py`,
   not inside the component folder.
2. **One place mounts everything:** `backend/app/modules/wiring.py` exposes
   `mount_components(app)` + `start_components()` / `stop_components()`, called from
   `app/main.py` (routers) and its `lifespan` (schedulers). Each component has an on/off env flag
   (`ENABLE_CROP_RESCUE`, `ENABLE_FORECAST`, `ENABLE_ROUTE_OPTIMIZER`), default **off**, so a broken
   component can be switched off on FastAPI Cloud without a code change.
3. **URLs:** mount with `prefix="/api/v2"` → `/api/v2/rescue/...`, `/api/v2/forecast/...`,
   `/api/v2/routes/...`. Each keeps its own tag so it gets its own section in `/docs`.
4. **Login:** mount with `dependencies=[Depends(get_current_user)]` (our JWT). Components never do
   their own login and never use Supabase Auth.
5. **Who is the user:** components get the user only from a dependency that the host overrides:
   ```python
   async def current_user_public_id(user: User = Depends(get_current_user)) -> str:
       return str(user.public_id)          # UUID string — never the internal int id
   app.dependency_overrides[component.current_farmer_id] = farmer_public_id  # role-checked variant
   ```
   Use role-checked variants where the component is role-specific (Crop Rescue → FARMER; routes →
   FARMER / DELIVERY_AGENT / LOGISTICS_MANAGER).
6. **Database:**
   - Only **add** tables, each with the component prefix: `cr_` (Crop Rescue), `fc_` (forecaster),
     `ro_` (routes), `va_` (voice). Never alter, drop, or write to core tables from component SQL.
   - Users are stored as `user_public_id UUID`/`TEXT` with **no foreign keys** to core tables.
   - SQL files go in `backend/migrations/` with a number + prefix, are idempotent
     (`CREATE TABLE IF NOT EXISTS`), wrapped in `BEGIN; ... COMMIT;`, and are run by hand in the
     Supabase SQL editor (see `backend/migrations/README.md`). Enable RLS on new tables with no
     policies (the backend connects as the DB owner; the app never talks to these tables directly).
   - **Driver mismatch:** the main app uses async SQLAlchemy + `asyncpg`. A component that uses sync
     SQLAlchemy + `psycopg` must get its **own** URL env var (e.g. `CR_DATABASE_URL=postgresql+psycopg://…`,
     session pooler port 5432, `?sslmode=require`). Never pass the main async `engine` to it and
     never let it fall back to our `DATABASE_URL` (that URL says `asyncpg` and will fail).
7. **Reading core data** (farms, listings, buyers, deliveries): the component must not query core
   tables itself. The host passes data in — either through a small adapter function in
   `wiring.py` that uses our repositories, or through a SQL **view** the component reads
   (e.g. `cr_buyer_pool` defined over `users` + `buyer_demand_requests`). A view is "adding", so it's
   allowed.
8. **Dependencies:** add the component's runtime requirements to `backend/requirements.txt` with
   version ranges. No big ML libraries in the main backend — heavy models run as separate services
   (the forecaster does).
9. **Env vars:** each component uses its own prefix (`CR_`, `FC_`/`FORECASTER_`, `RO_`, `VA_`).
   Add them, with safe placeholder values, to `backend/.env.example`, and tell Atharv which ones to
   set on FastAPI Cloud.
10. **Flutter:** each component's Dart client is constructed with `ApiClient().dio` so the base URL,
    token and refresh are shared. Paths include `/api/v2`. No user ids in calls.
11. **Failure isolation:** background jobs are wrapped in `try/except` + `logger.exception` and use
    `max_instances=1, coalesce=True`. A component error must never stop the main backend from
    starting — if its config is wrong, log clearly and leave it unmounted.

## Integration checklist (use for every component — `/integrate <name>` walks through it)

- [ ] Read the component's own README / INTEGRATION.md / CLAUDE.md at the pinned commit.
- [ ] Copy the package into `backend/app/modules/<name>/`; record the source commit hash in
      `docs/STATUS.md`.
- [ ] Add requirements; fresh-venv install works.
- [ ] Add the SQL file(s) to `backend/migrations/` (prefixed, idempotent, add-only). Show Atharv the
      exact file to run in Supabase; don't run it yourself against the main DB.
- [ ] Wire it in `wiring.py`: flag, mount under `/api/v2`, login dependency, identity override,
      scheduler start/stop.
- [ ] Env vars in `.env.example`.
- [ ] Tests in `backend/tests/modules/test_<name>.py`: mounted routes exist; no token → 401;
      another user's row → 404; flag off → routes absent.
- [ ] `/docs` shows the new section; the app still starts with the flag off **and** on.
- [ ] Flutter: Dart client using `ApiClient().dio`, URLs in `api_config.dart`, provider switched from
      demo data.
- [ ] `security-reviewer` agent review; update `docs/STATUS.md`.
