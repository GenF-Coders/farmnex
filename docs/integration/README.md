# Plugging components into the main app — shared contract

Four components are built in their own repos and then plugged into this app. This file is the set of
rules they all follow here; each also has its own guide in this folder.

| Component | Repo (checked 2026-09-29) | Shape | Tables | URL here | Budget |
|---|---|---|---|---|---|
| Crop Rescue | `farmnex_crop_rescue` @ `93eec60` | router package copied into `backend/app/modules/crop_rescue/` | `cr_` | `/api/v2/rescue/…` | 6–8 h |
| AI forecaster | `farmnex_ai_forecaster` @ `2f6f170` | **separate service** + small connector router here | `fc_` | `/api/v2/forecast/…` | 5–6 h |
| Route optimizer | `farmnex_route_optimization` @ `22d4859` | package `farmnex_routes` (pip from git, pinned) | `rt_` | `/api/v2/routes/…` + `/api/v2/logistics/…` | 10–14 h |
| Voice assistant | not reviewed yet | **separate service** calling our API as the user | `va_` | — | stretch |

## The picture

```
Flutter app ──(FarmNex login token)──► main FastAPI backend  /api/v2/...
                                         ├─ core routes (users, farms, listings, orders, ...)
                                         ├─ app/modules/crop_rescue         → /api/v2/rescue/...
                                         ├─ farmnex_routes (pip) + guard    → /api/v2/routes/...
                                         ├─ app/modules/forecast (connector) → /api/v2/forecast/...
                                         │        └──(server key)──► forecaster service (Render)
                                         └─ same Supabase PostgreSQL (new prefixed tables only)
voice assistant service (separate) ──(the user's own FarmNex token)──► /api/v2/...
```

The app only ever talks to **our** backend (plus the voice service for audio). Separate services'
keys live only on the server.

## Rules

1. **Where the code goes:** copied router packages live in `backend/app/modules/<name>/` (create
   `backend/app/modules/__init__.py`), **except** `farmnex_routes`, which must keep that exact import
   name (see its guide). Keep component files unchanged so updates can be re-copied; put all
   FarmNex glue in `backend/app/modules/wiring.py` (and `logistics_host.py` for routes).
2. **One place mounts everything:** `wiring.py` exposes `mount_components(app)`,
   `start_components()`, `stop_components()`, called from `app/main.py` and its `lifespan`. Each
   component has an on/off env flag (`ENABLE_CROP_RESCUE`, `ENABLE_FORECAST`,
   `ENABLE_ROUTE_OPTIMIZER`), **default off**.
3. **Import inside the mount function**, after the flag check — never at the top of a file. Some
   components read their settings the moment they're imported; a bad value must not stop the main
   backend from starting.
4. **URLs:** mount with `prefix="/api/v2"`; each keeps its own tag (own section in `/docs`).
5. **Login:** every component route needs `Depends(get_current_user)` (our JWT) unless its guide
   says otherwise (only the route tracking page). Components never do their own login and never use
   Supabase Auth.
6. **Who is the user:** always `str(user.public_id)` (UUID string) — never the internal int id.
   Components get it only from a dependency the host overrides, or from host code that passes it in.
   Being logged in is not enough: each guide lists who may call what.
7. **Database:**
   - Only **add** tables, with the component prefix: `cr_`, `fc_`, `rt_`, `va_`. Never alter, drop,
     or write to core tables from component SQL.
   - Users stored as text/UUID ids with **no foreign keys** to core tables.
   - SQL files go in `backend/migrations/` (numbered, idempotent, `BEGIN; … COMMIT;`), run by hand
     in the Supabase SQL editor (see `backend/migrations/README.md`). Turn off component auto-create
     where it exists, so tables come from these files.
8. **Sync vs async — the #1 cause of integration bugs here.** Our backend is **async**
   (`asyncpg`, `postgresql+asyncpg://…`). Crop Rescue and routes are **sync** (`psycopg`).
   - Give each sync component its **own** DB URL env var (`CR_DATABASE_URL`, `ROUTES_DATABASE_URL`)
     using the Supabase **session pooler** (port 5432) with `?sslmode=require`. Never let one fall
     back to our `DATABASE_URL` (fails with `MissingGreenlet` or dialect errors) or to SQLite.
   - Never pass our async `engine` into a component.
   - From our `async def` code, call a component's sync helpers with `await run_in_threadpool(...)`.
   - From a component's sync callback back into our async code: `anyio.from_thread.run(async_fn, …)`
     (works inside FastAPI worker threads; not from scheduler threads).
9. **Reading core data:** components never query core tables. The host passes data in (adapter
   function in `wiring.py` using our repositories) or through an added SQL **view**.
10. **Dependencies:** add runtime requirements with version ranges; components installed from git
    are **pinned to a commit hash**, never `@main`. No big ML libraries in the main backend.
11. **Env vars:** each component has its own prefix. Add them with safe placeholders to
    `backend/.env.example` and list which ones Atharv must set on FastAPI Cloud.
12. **Load `.env` before anything else.** Our settings class reads `.env` itself but doesn't put the
    values into the process environment, and some components read `os.environ` directly. So the
    first lines of `app/main.py` must be:
    ```python
    from dotenv import load_dotenv
    load_dotenv()          # before any other app / component import
    ```
    (FastAPI Cloud sets real env vars, so production works either way — this is for local runs.)
13. **Flutter:** every component client is built on `ApiClient().dio` (token + refresh shared),
    paths include `/api/v2`. For slow endpoints (forecaster cold start), pass a longer timeout on that
    request only: `Options(receiveTimeout: const Duration(seconds: 100))` — the default is 20 s.
14. **Failure isolation:** background jobs wrapped in `try/except` + `logger.exception`,
    `max_instances=1, coalesce=True`. A component with bad config logs one clear error and stays
    unmounted; the main backend still starts.

## Common failures (all components)

| Symptom | Likely cause | Fix |
|---|---|---|
| Backend won't start after adding a component | Import at top of file + bad env value | Import inside `mount_components`; fix the env var named in the error |
| Component works locally, not on FastAPI Cloud (or the reverse) | Env var set in `.env` only, or only on the cloud | Set on both; `load_dotenv()` first |
| `MissingGreenlet` / `asyncpg` errors inside a component | It got our async `DATABASE_URL` | Its own `*_DATABASE_URL` with plain `postgresql://` / `postgresql+psycopg://` |
| Data "disappears" after a redeploy | Component fell back to SQLite | Set its DB URL; wiring refuses SQLite |
| Whole API freezes while one request runs | Sync DB call inside `async def` | `run_in_threadpool` |
| 401 on every component call from the app | Built a new `Dio()` without the token | Use `ApiClient().dio` |
| App shows "timeout" on first forecast | 20 s Dio timeout vs ~60 s cold start | Longer timeout on that call + warm the service before the demo |
| Route shows twice / missing in `/docs` | Mounted twice, or flag off | One `mount_components` call; check flags |
| `relation "cr_…" does not exist` | SQL file not run on this database | Run the file in Supabase; auto-create off is expected |

## Integration checklist (`/integrate <name>` walks through it)

- [ ] Read the component's README / INTEGRATION / CLAUDE.md at the commit in the table above (or
      newer — then update the table and its guide).
- [ ] Install (copy or pinned pip); record the commit in `docs/STATUS.md`.
- [ ] SQL file(s) in `backend/migrations/`; show Atharv the exact file to run. Don't run it yourself.
- [ ] Wiring: flag, import inside mount, `/api/v2` prefix, login, identity/ownership rules, own DB
      URL checked, scheduler start/stop.
- [ ] `.env.example` updated.
- [ ] Tests in `backend/tests/modules/test_<name>.py`: routes exist when on / absent when off; app
      starts when config is missing; no token → 401; another user → 404.
- [ ] Start the backend with the flag off and on; `/docs` loads both times.
- [ ] Flutter client on `ApiClient().dio`; provider off demo data.
- [ ] `security-reviewer` review; update `docs/STATUS.md`.
