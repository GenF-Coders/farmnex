# AI forecaster → main app

**Source repo:** `atharvpatil1733-art/farmnex_ai_forecaster` (commit: see `docs/STATUS.md` → Components).
**What it does:** 1–3 day mandi price forecasts (low / expected / high), HIGH/NORMAL/LOW demand per
crop and district, best market + day to sell after transport cost, and which crop to sow. Scope:
Pune-district mandis; Onion, Tomato, Potato (more via its `config.yaml`). Real data from CEDA
Agmarknet (non-commercial licence — the CEDA credit must be shown).

Follow the shared rules in `README.md` in this folder. This file lists what's specific.

**Time budget (prototype):** ~5–6 h — deploy the service (1 h), connector + table + tests (2 h),
Flutter (2–3 h).

## Shape

The forecaster is a **separate service** (LightGBM + pandas — too heavy for the main backend). It runs
on its own host (its guide uses Render) and is protected by `X-API-Key`. The main backend gets a small
**connector router** that forwards calls with the key, checks the login, and logs answers.

```
Flutter ──FarmNex JWT──► /api/v2/forecast/* (connector, main backend) ──X-API-Key──► forecaster
                                   └── writes fc_forecast_logs (Supabase)
```

## Important: the kit was written for Supabase Auth — FarmNex doesn't use it

The forecaster's `integration/` kit assumes the app logs in with **Supabase Auth**. FarmNex has its
**own** JWT login and its own `users` table. Using the kit as-is would break in three ways:

| Kit file | Problem here | What to do |
|---|---|---|
| `integration/backend/farmnex_forecast.py` → `current_user_id` | Checks the token with Supabase Auth. Our `.env` already has `SUPABASE_URL` (for storage), so it **would be active** and reject every FarmNex token with 401. | Replace with our dependency: `str(user.public_id)` from `get_current_user`. Delete the Supabase Auth check. |
| `integration/supabase/001_forecast_logs.sql` | `user_id uuid references auth.users` — our users aren't in `auth.users`; RLS policy uses `auth.uid()`. | Use our own `backend/migrations/020_fc_forecast_logs.sql` (below). Don't run the kit's SQL. |
| `_save_log` (posts to Supabase REST with `SUPABASE_SERVICE_ROLE_KEY`) | Different key name from ours (`SUPABASE_SECRET_KEY`), and a different table. | Insert into `fc_forecast_logs` through our async DB session (a tiny repository), never failing the user's request. |
| `integration/flutter/lib/services/forecast_api.dart` | Uses `supabase_flutter` for the token and raw `http`. We don't have `supabase_flutter`. | Rewrite to take `ApiClient().dio` (token + refresh handled), paths `/api/v2/forecast/...`. |

Because of this, the connector is **adapted** (not copied unchanged) into
`backend/app/modules/forecast/router.py`. Keep its routes, request/response shapes, timeouts and
meta cache the same so the forecaster's docs still match.

## Table

`backend/migrations/020_fc_forecast_logs.sql`:
```sql
BEGIN;
CREATE TABLE IF NOT EXISTS public.fc_forecast_logs (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_public_id   UUID,                 -- FarmNex users.public_id, no FK on purpose
    kind             TEXT NOT NULL CHECK (kind IN ('price','demand','sell_options','crops')),
    request          JSONB NOT NULL,
    response         JSONB NOT NULL,
    data_as_of       DATE
);
CREATE INDEX IF NOT EXISTS fc_forecast_logs_user_idx ON public.fc_forecast_logs (user_public_id, created_at DESC);
CREATE INDEX IF NOT EXISTS fc_forecast_logs_kind_idx ON public.fc_forecast_logs (kind, created_at DESC);
ALTER TABLE public.fc_forecast_logs ENABLE ROW LEVEL SECURITY;  -- no policies: only the backend reads/writes
COMMIT;
```

## Where the forecaster runs, and keeping it awake

**Why a separate service at all:** the forecaster loads machine-learning libraries (LightGBM, pandas,
statsmodels, SHAP). Putting them inside the main backend would make every backend deploy slower and
heavier, and a model problem could take the whole marketplace down. As its own small service it can
fail or restart without touching logins, orders or payments — and "ML runs as a separate
microservice" is a good architecture point to show judges.

**Render free plan behaviour** (Render docs): a free web service **spins down after 15 minutes with no
requests**, and waking it takes **about a minute**. Each workspace gets 750 free instance hours per
month — enough for **one** service running all month.

Pick one:
1. **Render free + a keep-awake ping (₹0, recommended for the prototype):** use a free uptime
   monitor (e.g. UptimeRobot or cron-job.org) to open `https://<forecaster>/health` every 10 minutes,
   so it never reaches 15 idle minutes. Turn it on a day before judging and keep it on. Use only for
   this one service (the 750 free hours cover one always-on service).
2. **Render Starter (paid, about $7/month):** never sleeps; nothing else to set up. Good for the
   finale month.
3. **Still add the safety net either way:** longer timeout on forecast calls in the app (100 s) with a
   "waking up the forecaster…" message, and open `/health` 5 minutes before any demo.

## Steps

1. Deploy the forecaster (its `integration/INTEGRATION.md` Step 1) and set up option 1 or 2 above.
   Check `https://<host>/health`.
2. Add `backend/migrations/020_fc_forecast_logs.sql` (above); Atharv runs it in Supabase.
3. Create `backend/app/modules/forecast/router.py` from the kit's `farmnex_forecast.py` with the
   three changes in the table. Read config through our settings/env: `FORECASTER_URL`,
   `FORECASTER_API_KEY`. Keep one shared `httpx.AsyncClient` with the kit's timeouts (the free host
   sleeps; first call can take ~1 minute).
4. Host file `backend/app/modules/forecast_host.py` (loaded by `wiring.py` when `ENABLE_FORECAST=true`;
   don't edit `wiring.py`): mount under `/api/v2` with
   `dependencies=[Depends(get_current_user)]` (this also makes `/meta` and `/health` need login —
   fine, the app is logged in). Refuse to mount if `FORECASTER_URL`/`FORECASTER_API_KEY` are unset.
5. `.env.example`: `ENABLE_FORECAST=false`, `FORECASTER_URL=`, `FORECASTER_API_KEY=`.
6. Tests `backend/tests/modules/test_forecast.py` using `httpx.MockTransport` for the forecaster (no
   network): no token → 401; forecaster down → friendly 503; a log row is written with the caller's
   `public_id`; the API key never appears in responses or logs.
7. Flutter: new `lib/core/network/forecast_api.dart` built on `ApiClient().dio`; wire
   `lib/widgets/dialogs/ai_forecast_dialog.dart` and the market screen/ticker
   (`lib/widgets/apmc_ticker.dart`) to it; fill dropdowns only from `/forecast/meta`; show `reason`
   bullets and "based on mandi data up to <as_of>"; show the CEDA credit (kit's `ceda_credit.dart`,
   logo in `assets/`) on every screen with these prices. Remove the old `aiPricePredictionEndpoint`.
8. Existing `ai_predictions` / `ai_recommendations` tables: leave them alone for now; don't write
   forecaster output into them unless Atharv decides to (they're core tables).

## What can go wrong (and how you'll notice)

| Symptom | Cause | Fix |
|---|---|---|
| App says "timeout" on the first forecast, works on retry | Render free plan sleeps; wake-up ~60 s, but our Dio timeout is 20 s | Forecast calls pass `Options(receiveTimeout: const Duration(seconds: 100))`; show "waking up the forecaster…"; **open `/health` 5 minutes before judging**; Starter plan if budget allows |
| Every forecast call 401 | Kit's Supabase Auth check left in | Use our `get_current_user` (step 3) |
| 503 "temporarily unavailable" | Wrong `FORECASTER_URL`, or key mismatch | Key must equal `FARMNEX_FORECASTER_API_KEY` on Render exactly (no spaces/quotes) |
| Logs say "could not save forecast log" | `fc_forecast_logs` not created | Run `020_fc_forecast_logs.sql`; the user still gets the forecast |
| "unknown market/crop" | App sent a name not in `/forecast/meta` | Fill dropdowns only from `/forecast/meta`; don't hard-code names |
| "synthetic data is hidden" | No real data for that market × crop | Offer only crops listed under that market in `/meta` |
| Render build fails with `libgomp.so.1` | LightGBM needs a system library | See the forecaster repo's INTEGRATION.md troubleshooting |
| Env vars ignored locally | `.env` not loaded into `os.environ` | `load_dotenv()` first in `main.py` (shared rule 12) |
| Judges ask about data licence | CEDA non-commercial terms | CEDA credit visible on every forecast screen |

## Done when

- `/docs` shows **forecast** under `/api/v2/forecast`.
- In the app: Pune + Onion shows 3 days of prices with reasons and the CEDA credit.
- A row appears in `fc_forecast_logs` with the user's `public_id`.
- With `ENABLE_FORECAST=false` the backend starts and the forecast routes are gone.
