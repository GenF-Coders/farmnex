# Backend rules (FastAPI)

Read the root `CLAUDE.md` first. This file adds backend-specific detail.

## Stack facts (checked 2026-09-29)

- Python 3.11+, FastAPI 0.141, Pydantic 2, SQLAlchemy 2 **async** with `asyncpg`.
- DB: Supabase PostgreSQL via `DATABASE_URL=postgresql+asyncpg://...` (`app/core/database.py`,
  `NullPool`). Tables are created at startup with `Base.metadata.create_all` (creates missing
  tables only; it never changes existing ones). There is no Alembic.
- Auth: our **own** phone-OTP login with RS256 JWTs (`app/core/security.py`), not Supabase Auth.
  Keys are loaded from `secrets/jwt_private.pem` / `jwt_public.pem`.
  `Depends(get_current_user)` (`app/api/dependencies/current_user.py`) returns the `User` ORM row
  with `user.role` already loaded. `user.id` is the internal int; `user.public_id` is the UUID.
- Roles (seeded in `app/main.py`): SUPER_ADMIN, ADMIN, MANAGER, STAFF, LOGISTICS_MANAGER,
  DELIVERY_AGENT, SUPPORT, VENDOR, BUYER, FARMER. Public sign-up allows only FARMER, BUYER, VENDOR.
- Storage: Supabase Storage via `app/services/storage_service.py` (server-side secret key).
- Errors: raise `app.core.exceptions` (`NotFoundError`, `ForbiddenError`, `ValidationError`,
  `ConflictError`, ...) from services; `main.py` turns them into JSON. (`app/services/exceptions.py`
  is an older second set used by users/farms/addresses — don't add a third.)

## Layering (keep it)

`endpoints/*_controller.py` (HTTP only) → `services/*_service.py` (rules + ownership) →
`repositories/*_repository.py` (SQL only). Controllers never query the DB directly. Services never
import FastAPI.

## Ownership pattern — copy this for every resource

The reference implementation is **farm crops**:
`endpoints/farm_crop_controller.py` + `services/farm_crop_service.py` +
`repositories/farm_crop_repository.py`. It does four things right:

1. The controller passes `current_user` into every service method.
2. **Create** sets the owner from the token (`"farmer_id": current_user.id`) and never from the body.
3. Related rows are referenced by **public UUID** in the request and resolved + ownership-checked in
   the service (`get_farm_owned_by_user(farm_public_id, current_user.id)`), then converted to the
   internal int id.
4. **Get/list/update/delete** use owner-filtered queries (`get_owned_by_public_id(public_id, user_id)`,
   `list_owned(user_id=...)`). Not yours → `NotFoundError` (404), so we don't reveal it exists.
   Update strips protected fields (`id`, `public_id`, owner id, `created_at`, `updated_at`).

For resources with two parties (orders, bids, reviews, disputes, deliveries), "owned" means "I am
one of the parties" and each action has its own rule (e.g. only the buyer cancels an order; only the
assigned agent adds a tracking event). The per-resource rules are in `docs/FIX_PLAN.md` F1.

Role checks: use one shared dependency, e.g.

```python
# app/api/dependencies/roles.py  (create it in FIX_PLAN F3)
def require_roles(*roles: str):
    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role is None or user.role.name not in roles:
            raise HTTPException(status_code=403, detail="Not allowed for your role.")
        return user
    return _check
```

## Schemas

- `*Create` / `*Update` models contain **only** fields the client may set. Server-owned fields
  (owner ids, `status` transitions, `paid_at`, totals, `winner_bid_id`, ...) are not in them.
- References to other rows use public UUIDs (`farm_id: UUID`), not internal ints.
- `*Response` never exposes internal int ids, hashes or storage paths; use `public_id` and signed URLs.

## Database changes

- A new core table = new model in `app/models/` **plus** import it in
  `app/domain_model_registry.py` so `create_all` sees it. Only new tables — never edit a column of
  an existing model that already exists in Supabase (create_all will not apply it, and the live table
  must not be altered anyway). If a change to an existing table is truly needed, stop and ask.
- Component tables (crop rescue, forecaster, routes, voice) are created by hand-run SQL files in
  `backend/migrations/` — see `backend/migrations/README.md`.

## Tests

- `python -m pytest -q` from `backend/`. DB tests must use `TEST_DATABASE_URL` (a throwaway
  Postgres, e.g. `docker run -p 5433:5432 -e POSTGRES_PASSWORD=test postgres:16`) and **skip** if it
  is not set. Never point tests at the Supabase URL.
- Every ownership fix needs a test: user A creates a row, user B gets 404 on read/update/delete and
  doesn't see it in the list. Build tokens with `create_access_token(...)` against test users.
- Before calling a task done: tests pass, the app imports (`python -c "import app.main"`), and
  `/docs` loads.

## Don'ts

- Don't add `allow_origins=["*"]` style shortcuts, broad `except Exception: return ok`, or
  `print()` debugging (use `logging`).
- Don't return raw exception text to clients (e.g. `/db` currently does — FIX_PLAN F6).
- Don't use `psycopg2` (needs system build tools). Sync components use `psycopg[binary]` (v3).
- Don't pass the main async engine into a component that expects a sync `Engine`.
