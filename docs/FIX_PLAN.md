# FarmNex fix plan

From the code review on 2026-09-29. Work top to bottom: **P0 before any demo**, then P1, then the
rest. Use `/fix <ID>` in Claude Code to work one item. When an item is done, tick its box, and add a
line to `docs/STATUS.md`.

Each item says **why** (in plain words), **what to do**, and **how to check** it's really fixed.

---

## P0 — Security (must fix before any demo or judging)

### - [ ] F1. Ownership checks on 22 modules

**Why:** these modules only check that someone is logged in, not *whose* data it is. Any logged-in
user can list every payment, edit anyone's bid, delete other people's orders, or read the audit log.

**Affected controllers** (all in `backend/app/api/v2/endpoints/`, all generated from one template —
they contain the comment "Ownership/authorization rules beyond the direct actor field belong in the
domain service"):
`ai_prediction, ai_recommendation, audit_log, bid, bid_event, buyer_demand_request, crop_batch,
crop_type, delivery, delivery_proof, delivery_tracking_event, farm_crop_activity, notification,
order, order_dispute, order_item, payment, product_image, product_listing, review, waste_record,
waste_utilization_listing`.

Already correct (use as the pattern): `farm_crop` (best example), `farm`, `address`, `user`, `me`.

**What to do:** follow the ownership pattern in `backend/CLAUDE.md`. Do **one module per commit**, in
this order (demo-critical first): payment → bid → bid_event → order → order_item → product_listing →
product_image → delivery → delivery_tracking_event → delivery_proof → crop_batch →
farm_crop_activity → waste_record → waste_utilization_listing → buyer_demand_request → review →
order_dispute → notification → ai_prediction → ai_recommendation → crop_type → audit_log.

**Suggested rules** (confirm with Atharv before implementing a row; these are business decisions):

| Resource | Owner field(s) | Who can read | Create | Update | Delete |
|---|---|---|---|---|---|
| product_listings | `seller_id` | any logged-in user sees ACTIVE; seller sees all own | FARMER/VENDOR; farm + crop batch must be theirs | seller | seller (prefer status=CLOSED) |
| product_images | via listing `seller_id` | same as listing | seller of the listing | seller | seller |
| crop_batches | via `farm_crop.farmer_id` | owner | owner of the farm crop | owner | owner |
| farm_crop_activities | via `farm_crop.farmer_id` | owner | owner | owner | owner |
| crop_types | reference data | any logged-in user | ADMIN | ADMIN | ADMIN (prefer deactivate) |
| buyer_demand_requests | `buyer_id` | owner; FARMERs see OPEN ones | BUYER | owner | owner |
| bid_events | `created_by_id` | anyone sees OPEN; creator sees own | seller of the listing | creator (not `status`/`winner_bid_id`) | creator, only if no bids |
| bids | `bidder_id` | bidder sees own; event creator sees bids on their event | BUYER, event OPEN, not own listing | none (withdraw = status change by server) | none |
| orders | `buyer_id` (+ sellers via order_items) | buyer; sellers of its items | BUYER; totals computed by server (F12) | buyer may cancel while PLACED | none |
| order_items | order buyer / item `seller_id` | buyer or that seller | only by the server with the order | seller: item status | none |
| payments | `payer_id` | payer; seller of the order (read); ADMIN | **server only** — remove public POST/PATCH/DELETE (F12) | server only | never |
| deliveries | `seller_id`, `delivery_agent_id`, order buyer | those three + LOGISTICS_MANAGER | seller or LOGISTICS_MANAGER | agent: status; manager: assign agent | none |
| delivery_tracking_events | via delivery | delivery parties | assigned agent | none | none |
| delivery_proofs | `uploaded_by_id`, via delivery | delivery parties | assigned agent | none | none |
| order_disputes | `raised_by_id`, `against_user_id` | both parties + SUPPORT/ADMIN | a party of the order | raiser: text; SUPPORT/ADMIN: status | none |
| reviews | `reviewer_id`, `reviewee_id` | any logged-in user (published) | buyer of a DELIVERED order, once per order | reviewer | reviewer |
| waste_records | `recorded_by_id`, farm | owner | FARMER; farm must be theirs | owner | owner |
| waste_utilization_listings | `seller_id` | anyone sees ACTIVE; owner sees own | owner of the waste record | owner | owner |
| notifications | `user_id` | own only | server only | own: mark read | own |
| ai_predictions | `user_id` | own; ADMIN | server only | none | none |
| ai_recommendations | `user_id` | own | server only | own: accept/dismiss | own |
| audit_logs | — | ADMIN/SUPER_ADMIN | server only | never | never |

"Server only" = remove that route from the public controller; the action happens inside another
service (e.g. a notification is created when a bid is placed).

**How to check:** for each module, a pytest test where user A creates a row and user B gets **404**
on get/update/delete and does not see it in the list; wrong role gets **403**. Then ask the
`security-reviewer` agent to review the module.

### - [ ] F2. Server-owned fields and public ids in request bodies

**Why:** request bodies accept fields the phone must never control, e.g. `PaymentCreate` accepts
`payer_id`, `status`, `paid_at`; bids accept `bidder_id`; orders accept `buyer_id` and totals. They
also take internal integer ids (`order_id: int`), which the app never receives (responses only show
`public_id`).

**What to do:** do it together with F1, per module: remove owner ids, status, timestamps, totals and
winner fields from `*Create`/`*Update` in `backend/app/schemas/`; take related rows as public UUIDs
and resolve them in the service (like `farm_crop_service.create`). Remove internal int ids from
`*Response` (use related `public_id`s). Also remove the duplicated import blocks inside the generated
schema files.
While no app uses them yet, also fix the misspelled URL prefixes: `/crop-batchs` → `/crop-batches`,
`/deliverys` → `/deliveries`, `/farm-crop-activitys` → `/farm-crop-activities`.

**How to check:** OpenAPI (`/docs`) shows no `*_id: integer` in request bodies and no owner/status
fields in create bodies; sending `payer_id` in a body is ignored or rejected.

### - [ ] F3. Role checks

**Why:** nothing checks roles today — a BUYER could create crop types or read audit logs.

**What to do:** add `app/api/dependencies/roles.py` with `require_roles(...)` (sketch in
`backend/CLAUDE.md`) and use it per the F1 table. Keep `role_controller` and `otp_controller`
unmounted as they are now (they're commented out in `api/v2/router.py`) unless Atharv asks.

**How to check:** tests: BUYER → 403 on `POST /api/v2/crop-types` and `GET /api/v2/audit-logs`;
ADMIN → allowed.

---

## P1 — Repo health and deployment

### - [ ] F4. Delete junk files
`backend/app.zip` (1.1 MB old copy of the backend with `__pycache__` and an old `api/v1`) and
`backend/0.141` (empty file created by an unquoted `pip install fastapi>=0.141`). Use `git rm`.
Add `*.zip` to `.gitignore`.
**Check:** `git ls-files | grep -E "app.zip|0.141"` prints nothing.

### - [ ] F5. Fix dependencies
`requirements.txt` has `psycopg2` (fails to build without Postgres dev tools — likely to break
deploys) and `PyMySQL` (unused, the DB is Postgres). It pins `uvicorn==0.52.4` but `pyproject.toml`
requires `uvicorn>=0.53` — they conflict. Remove `psycopg2` and `PyMySQL`, align uvicorn, and move
`pytest` to a dev section. Confirm which file FastAPI Cloud installs from and make that the source of
truth; keep the other consistent.
**Check:** fresh venv: `pip install -r requirements.txt` succeeds; `python -c "import app.main"` works.

### - [ ] F6. `/db` leaks error details
`GET /db` returns `str(exc)`, which can include the database host/user. Return only
`{"status":"error","database":"disconnected"}` and log the details server-side.
**Check:** with a bad `DATABASE_URL`, the response has no hostnames.

### - [ ] F7. CORS
`main.py` uses `allow_origins=["*"]` with `allow_credentials=True` and ignores the `CORS_ORIGINS`
setting. Use the settings value; credentials `False` (we use bearer tokens, not cookies). Mobile apps
don't need CORS; Flutter **web** builds do — include their origin.
**Check:** a request with `Origin: https://evil.example` gets no `Access-Control-Allow-Origin`.

### - [ ] F8. Settings that do nothing
`.env.example` lists rate limits and security headers, but `app/core/middleware.py`, `jwt.py`,
`logging.py`, `constants.py` are empty files. Either implement the minimum — security headers +
a simple in-memory rate limit on `/api/v2/auth/*` (fine for one instance; note it resets on restart)
— or remove the unused settings so nobody thinks they're active. Ask Atharv which.
**Check:** 6 rapid `login/request-otp` calls from one IP → the 6th gets 429 (if implemented).

### - [ ] F9. Supabase pooler + asyncpg check
`.env.example` uses port **6543** (Supabase *transaction* pooler). asyncpg's prepared-statement cache
breaks behind a transaction pooler (errors like `prepared statement "__asyncpg_stmt_1__" already
exists`). If production uses 6543, add `connect_args={"statement_cache_size": 0}` to
`create_async_engine` (and `prepared_statement_cache_size=0` in the URL query for SQLAlchemy), or use
the session pooler (5432). Ask Atharv what the production URL uses (don't read `.env`).
**Check:** 50 quick requests to `/api/v2/home` → no prepared-statement errors in logs.

### - [ ] F10. One entrypoint
`app/main_complete.py` + `app/api/v2/domain_router.py` mount the same controllers a second time
(duplicate routes/operation ids). Confirm FastAPI Cloud runs `app.main:app`; then delete those two
files. Keep `app/domain_model_registry.py` but import it from `app/main.py` so `create_all` always sees
every model.
**Check:** `/docs` lists each route once; `grep -r main_complete` finds nothing.

### - [ ] F11. Test setup + CI
Add `backend/tests/conftest.py` with a `TEST_DATABASE_URL` fixture (skip DB tests when unset), a
test-user + token factory, and an `httpx.AsyncClient` against the app. Add
`.github/workflows/backend-tests.yml` running pytest with a Postgres service container.
**Check:** CI is green on a PR.

---

## P2 — Core marketplace logic (plan with Atharv first; these are features)

### - [ ] F12. Real rules for orders, bids, pre-bidding and payments
Today these services are plain save/edit/delete. Needed:
- **Orders:** buyer from token; items reference listings; server computes prices, subtotal, fees,
  total; reduces `available_quantity` in the same transaction; status machine
  (PLACED → CONFIRMED → SHIPPED → DELIVERED / CANCELLED).
- **Bids / pre-bidding (7-day window):** bid only while the event is OPEN and within its time window;
  amount must beat the current highest by a minimum step; no bidding on your own listing; the server
  closes the event and sets `winner_bid_id`; write `bid_events` history; lock rows
  (`SELECT ... FOR UPDATE`) so two bids at once can't both "win".
- **Escrow:** winning pre-bidder pays a **20% advance** into the wallet; released to the farmer with
  the remainder only after the buyer confirms delivery (kept separate from direct sales).
- **Payments:** created only by the server from an order/bid flow; status machine
  (PENDING → HELD → RELEASED / REFUNDED / FAILED); idempotency key per attempt. For the prototype a
  clearly labelled "demo payment provider" is fine — never mark money as paid because the client said so.
**Check:** tests for each rule (double bid race, own-listing bid, total tampering, early release).

---

## P3 — Frontend

### - [ ] F13. Connect screens to the backend
Only login, profile and farm-file upload use the backend. Connect one provider per PR with
`/connect-screen <name>`, in this order: `listing` + `market` (marketplace) → `cart` + `payment`
(checkout, after F12) → `bidding` → `rescue` (after Crop Rescue integration) → `logistics` (after
route optimizer) → `waste` → `admin` → `verification` / `crop_media`.
Remove dead URLs from `api_config.dart` (`/api/crops`, `/api/ai/*`, `/api/rescue/request`,
`/api/waste/listings`, `/ws/bidding/*`) as each feature gets its real endpoint. The fake
`core/payments/payment_gateway.dart` must not stay the default once real payments exist.
**Check:** the screen shows backend data; airplane mode shows a friendly error + retry.

### - [ ] F14. Store tokens securely
Move access/refresh tokens from `shared_preferences` to `flutter_secure_storage` (keep language and
onboarding flags in shared_preferences). Migrate: read old keys once, save securely, delete old.
**Check:** log in, restart the app → still logged in; old prefs keys are gone.

### - [ ] F15. Made-up names in demo data
`bidding_provider.dart` (and possibly others) uses real company names like "Godrej Agrovet" and
"Adani Wilmar" as "verified buyers". Replace with fictional names across `lib/`.
**Check:** `grep -rniwE "godrej|adani|reliance|tata|itc|mahindra" frontend/lib` finds nothing.

### - [ ] F16. One README per app
`frontend/` has `README.md`, `README_original.md`, `README_FINAL.md`, `README_HTML_REBUILD.md`,
`CHANGES.md`, `LANGUAGE_AND_API_UPDATE.md`, `FARMNEX_V2_INTEGRATION.md`. Merge what's still true
into `frontend/README.md`; delete the rest. Update the root `README.md` "run locally" section.
**Check:** one README per folder; setup steps work on a fresh clone.

---

## Not checked in the review

- `flutter analyze` / `flutter test` were not run (no Flutter SDK in the review environment).
  Run them once and add any errors here as new items.
- Production config on FastAPI Cloud (which entrypoint, which DB port) — ask Atharv.
