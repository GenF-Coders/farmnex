# Copy-paste prompts for Claude Code

Use with `docs/FINALE_PLAN.md` (who does what, when). Rules:
- **One fresh Claude Code session per prompt** (fewer mistakes, less usage).
- **Merge the PR before the next prompt** in the same stream.
- 🧑 = something a person must do by hand; Claude Code will remind you.
- Each prompt shows its **time budget**. If it runs 50% over, stop and ask the team lead.

---

## Step 0 — first session (any stream, no changes)

```
Read CLAUDE.md, docs/FINALE_PLAN.md, docs/FIX_PLAN.md and docs/STATUS.md. In simple words, tell me the plan, what my stream does first, and anything that looks risky. Don't change anything.
```

---

## Stream A — Backend core & security

**A1. Junk files** (15 min)
```
/fix F4
```

**A2. Dependencies** (30 min) — it will ask which file FastAPI Cloud installs from; answer "requirements.txt" if unsure.
```
/fix F5
```

**A3. Load .env first + component settings list** (15 min)
```
/fix F17
```

**A4. Test setup** (2 h)
```
/fix F11 — if Docker isn't available here, install PostgreSQL inside this session for the test database. Never use the Supabase database for tests. Keep the test helpers small: a test database fixture, a make-user-with-role helper, a make-token helper, and an HTTP client.
```

**A5. Roles** (30 min)
```
/fix F3
```

**A6. Unmount unused modules** (30 min)
```
/fix F1 fast path — show me the list of modules you'd unmount and why each isn't needed for the demo. Wait for my OK, then remove only those from the modules list in api/v2/router.py. Don't delete any files or tables.
```

**A7. Ownership, one module at a time** (~30–45 min each)
```
/fix F1 payment — do F2 for payments in the same change. First show me the rules from the F1 table for payments and wait for my OK.
```
Repeat with the next module name, in this order (skip any you unmounted in A6):
`bid` → `bid_event` → `order` → `order_item` → `product_listing` → `product_image` → `crop_batch` → `waste_record` → `waste_utilization_listing` → `buyer_demand_request` → `notification` → `crop_type`
Small ones can share a session: `/fix F1 notification and crop_type — ...`

**A8. Pooler check + small fixes** (1.5 h, one session each)
```
/fix F9 — ask me which port the production DATABASE_URL uses. Don't read .env.
```
```
/fix F6
```
```
/fix F7 — we use the Android app; ask me if we also deploy the Flutter web build.
```
```
/fix F10 — ask me to confirm FastAPI Cloud runs app.main:app before deleting anything.
```

**A9. Marketplace logic — plan first** (≈8 h total)
```
/fix F12 — build only the "Prototype minimum" in FIX_PLAN. First explain the flow in simple words (order → confirmed → delivered; pre-bid → winner → 20% hold → release on delivery) with the status steps and the new wallet_ledger table. Wait for my OK before writing code.
```
Then, one per session:
```
Continue F12: orders only (server totals, stock, statuses), with tests.
```
```
Continue F12: bids and pre-bid close (no double winners — test two bids at the same time), with tests.
```
```
Continue F12: wallet_ledger + demo payment (hold 20% on win, release once on delivered), with tests. Give me the SQL file for wallet_ledger to run in Supabase.
```
🧑 Run the wallet_ledger SQL in Supabase (or confirm it's created by create_all — Claude will say which).

**A10. Security review of everything** (2 h)
```
Act as a hackathon judge who tests security. Ask the security-reviewer agent to review every mounted endpoint and all integrated components, trying to access one user's data as another user. Explain the findings simply, then fix everything marked HIGH, one commit each.
```

---

## Stream B — Components

**B1. Crop Rescue: finish its Phase 5 — in the `farmnex_crop_rescue` repo** (1 h)
```
/build-phase 5 — first read docs/FARMNEX_HOST.md in this repo and follow it where it differs from SPEC.md (farmer id = users.public_id, own CR_DATABASE_URL, never pass the host's async engine).
```

**B2. Forecaster: put it online** (1 h) 🧑 Follow Step 1 of `integration/INTEGRATION.md` in the `farmnex_ai_forecaster` repo (Render). Check `https://<your-render-url>/health` shows `"status":"ok"`.

**B3. Crop Rescue into the main app** (2–3 h)
```
/integrate crop-rescue — the source is the farmnex_crop_rescue repo at its latest main commit.
```
🧑 Run `010_cr_crop_rescue.sql` and `011_cr_demo_seed.sql` in Supabase. Set on FastAPI Cloud: `ENABLE_CROP_RESCUE=true`, `CR_DATABASE_URL` (session pooler, psycopg form), `CR_ENABLE_SIMULATE=true`.

**B4. Forecaster into the main app** (2 h)
```
/integrate ai-forecaster — the forecaster is deployed at <paste your Render URL>. Our login is FarmNex's own JWT, not Supabase Auth; follow the "Important" table in the guide.
```
🧑 Run `020_fc_forecast_logs.sql`. Set `ENABLE_FORECAST=true`, `FORECASTER_URL`, `FORECASTER_API_KEY` on FastAPI Cloud.

**B5. Route optimizer backend** (5–6 h, two sessions)
```
/integrate route-optimizer — part 1: install farmnex_routes pinned to the commit in the guide, SQL file, wiring with the ROUTES_DATABASE_URL checks, the allow-list + ownership guard, and the vehicle host endpoints. Tests for the guard. Stop before Slip 2/3.
```
🧑 Run `030_rt_route_tables.sql`. Set `ENABLE_ROUTE_OPTIMIZER=true`, `ROUTES_DATABASE_URL`, `ROUTES_AUTO_CREATE_TABLES=false`, `ROUTES_PUBLIC_BASE_URL=https://farmnex.fastapicloud.dev`.

After Stream A finishes A9 (orders):
```
/integrate route-optimizer — part 2: Slip 2 (CONFIRMED order → load, with the coordinate and weight checks) and Slip 3 (listener → order DELIVERED → wallet release once), following the guide. Tests.
```

**B6. Component screens** (one session each)
```
/connect-screen rescue — use the Crop Rescue Dart client on ApiClient().dio, paths under /api/v2/rescue.
```
```
Connect the AI forecast dialog and the APMC ticker to /api/v2/forecast (docs/integration/ai-forecaster.md step 7). Use a 100-second timeout only for forecast calls and show "waking up the forecaster…" while waiting. Show the CEDA credit.
```
```
/connect-screen logistics — driver flow from docs/integration/route-optimizer.md "Flutter": vehicle, go online, trip, stop buttons, GPS ping only while the trip screen is open, and a Track button that opens tracking_url in a WebView. Add geolocator and webview_flutter.
```

**B7. Demo seed** (1 h)
```
Prepare demo data for the route optimizer against production: one driver vehicle near Pune and three pending loads from two farmers to the same buyer, using our host endpoints (not the component's blocked routes). Write the steps into docs/DEMO.md.
```

---

## Stream C — Flutter core

**C1. Quick fixes** (2 h total, one session each)
```
/fix F15
```
```
/fix F16
```
```
/fix F14
```

**C2. Screens** (after the backend part is fixed — see FINALE_PLAN dependencies)
```
/connect-screen listing
```
```
/connect-screen market
```
```
/connect-screen bidding
```
```
/connect-screen cart
```
```
/connect-screen payment — use the demo payment from F12; label it "Pay (demo)".
```
```
/connect-screen waste
```

**C3. Demo accounts** (1 h)
```
List the demo accounts we need (FINALE_PLAN "Demo safety kit") and how to create each one through the app or the API. Don't create them in the database directly.
```

---

## Voice (stretch — only after Checkpoint 2 if on budget)

In the voice assistant repo:
```
Read docs/integration/voice-assistant.md from the farmnex_main repo. Build the FarmNex domain pack with read-only tools only (price forecast, demand, rescue alerts): check FarmNex tokens with the public key only, and call the main API with the user's own token. Show me the plan first. Budget 8 hours.
```
Then in farmnex_main:
```
/integrate voice-assistant
```

---

## Final hours (everyone)

```
Write docs/DEMO.md: a 5-minute demo script for the story in FINALE_PLAN (listing → pre-bid → Crop Rescue alert + forecast → confirmed order → pooled route → tracking → payment released), with demo accounts and exact taps. Check each endpoint it uses responds on production.
```
```
Run /check and a full demo dry-run checklist against production. List anything broken, most demo-critical first. Don't fix yet.
```

---

## Anytime

```
Explain that again more simply, like I'm new to coding.
```
```
Here's the error: <paste>. Find the cause, explain it simply, and fix it. Don't change unrelated code.
```
```
Read docs/STATUS.md, docs/FIX_PLAN.md and docs/FINALE_PLAN.md. What's done, what's left in my stream, and are we on budget?
```
```
/check
```
