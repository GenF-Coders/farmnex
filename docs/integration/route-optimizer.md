# Route optimizer → main app

**Source repo:** `atharvpatil1733-art/farmnex_route_optimizer` (being built; it could not be read
during the 2026-09-29 review, so **check this file against that repo's README/CLAUDE.md before
integrating** and update anything that differs).
**What it does (planned):** pools nearby farmers' loads going to the same buyers, fills return trips
(backhaul), suggests a nearby transporter or lets the farmer self-deliver, and quotes fares from each
vehicle's current rate for the load carried. No background GPS.

Follow the shared rules in `README.md` in this folder. This file lists what's specific.

## What already exists in the main app (so the component doesn't duplicate it)

| Thing | Where | State |
|---|---|---|
| Roles `DELIVERY_AGENT`, `LOGISTICS_MANAGER` | seeded in `backend/app/main.py` | real |
| `deliveries` table: `order_id`, `seller_id`, `farm_id`, `delivery_agent_id`, `status`, `pickup_address_snapshot`, `delivery_address_snapshot`, `expected_at`, `delivered_at` | `backend/app/models/delivery.py` | real, but no ownership checks yet (FIX_PLAN F1) |
| `delivery_tracking_events`, `delivery_proofs` | models + controllers | real, no ownership checks yet |
| Farm & address coordinates (`latitude`, `longitude`) | `farms`, `addresses` | real |
| Vehicles (type, capacity, rates) | — | **not in the backend**. Only demo data in Flutter `lib/providers/logistics_provider.dart` |
| Driver screens (loads, active trip, earnings) | `lib/screens/logistics/logistics_screens.dart` | Flutter UI on demo data |

So the component needs its own **vehicle** table (`ro_vehicles`) — that's "adding", which is allowed.

## Contract the component should follow (same as Crop Rescue)

- Package `route_optimizer/` with public names: `router`, `settings`, `current_user_ref`
  (+ `start_scheduler`/`stop_scheduler` only if it has background jobs).
- Router prefix `/routes`, tag `route-optimizer` → mounted at **`/api/v2/routes/...`**.
- Relative imports only; no `from app...`; no `FastAPI()` inside; no auth inside.
- Tables `ro_*` only, e.g. `ro_vehicles` (owner `user_public_id`, type, capacity_kg, rate_per_km,
  min_fare, home lat/lon, is_available), `ro_trip_plans`, `ro_trip_stops`, `ro_quotes`. No FKs to core
  tables; users as `user_public_id`; deliveries as `delivery_public_id`.
- Pure algorithm code (distance, pooling, backhaul matching, fare) in `core/` with unit tests and no
  DB access — easiest to test and to explain to judges.
- If it's sync + psycopg like Crop Rescue: its own `RO_DATABASE_URL` (see README rule 6).

## How it gets core data (host adapter — rule 7)

The component must not read `deliveries`, `farms` or `addresses` itself. Pick one:
- **Adapter function (recommended):** in `backend/app/modules/wiring.py`, write
  `async def open_loads_for(user) -> list[LoadIn]` that uses our repositories and ownership rules to
  build plain objects (pickup lat/lon, drop lat/lon, weight, ready time, delivery public_id), and pass
  them into the component's planning function / endpoint. The component defines `LoadIn`.
- **Read-only view:** `ro_open_loads` view over `deliveries` + `farms` + `addresses` in a
  `backend/migrations/03x_ro_views.sql` file.

Writing back: when a plan is accepted, assigning a driver means setting
`deliveries.delivery_agent_id` — do that **through our delivery service** (with its ownership/role
checks), called from the host glue, not by component SQL.

## Who can do what

| Action | Role |
|---|---|
| Register/edit own vehicle, set availability and rates | DELIVERY_AGENT (own vehicles only) |
| Ask for a quote / pooled plan for own deliveries; choose self-delivery | FARMER (own deliveries) |
| See loads offered to them, accept a trip, update stop status | DELIVERY_AGENT (only trips offered/assigned to them) |
| See all plans, re-assign | LOGISTICS_MANAGER, ADMIN |

Identity override: `current_user_ref` → `str(user.public_id)`; role checks in host dependencies.

## Steps

1. Read the component repo's docs; update this file if its contract differs.
2. Copy `route_optimizer/` → `backend/app/modules/route_optimizer/`; record the commit hash.
3. Requirements with version ranges (no OR-Tools unless really needed — it's large; check wheel
   availability on FastAPI Cloud first).
4. SQL: `backend/migrations/030_ro_route_optimizer.sql` (add-only, prefixed); Atharv runs it.
5. Wiring: flag `ENABLE_ROUTE_OPTIMIZER`, mount under `/api/v2` with login dependency, identity
   override, host adapter for loads.
6. `.env.example`: `ENABLE_ROUTE_OPTIMIZER=false` + its `RO_` settings.
7. Tests `backend/tests/modules/test_route_optimizer.py`: 401 without token; farmer can't plan
   another farmer's delivery (404); agent can't edit another agent's vehicle (404); fare maths for a
   known case.
8. Flutter: `RouteApi(ApiClient().dio)`; switch `logistics_provider.dart` from demo data; add vehicle
   registration form if not present; keep the three existing logistics screens.

## Done when

- A farmer gets a pooled plan + fare for two nearby deliveries to the same buyer.
- A driver sees the load, accepts it, and the delivery shows that driver as assigned.
- Backend starts with `ENABLE_ROUTE_OPTIMIZER=false`.
