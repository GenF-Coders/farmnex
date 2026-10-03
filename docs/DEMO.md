# FarmNex demo — 5-minute script

The story (FINALE_PLAN): a farmer lists Tomatoes → a buyer pre-bids → Crop Rescue warns about spoilage
(with the AI price forecast) → an order is confirmed → a pooled truck route → the buyer tracks the
truck → on delivery the farmer is paid.

**No real phone numbers, tokens or keys are written here.** The six accounts are real team phones; the
numbers are on the private card. Every account logs in with a real one-time code on its phone.

## Accounts

| Name | Role | Used for |
|---|---|---|
| `FARMER_1` | Farmer (Hadapsar farm) | the on-stage farmer: listing, pre-bid, Crop Rescue, confirms order |
| `FARMER_2` | Farmer (Khadakwasla farm) | second pickup, so the route is pooled |
| `BUYER_1` | Buyer | checkout, Pay (demo), tracking, "Mark as received" |
| `BUYER_2` | Buyer | places a competing pre-bid |
| `DRIVER` | Delivery agent | owns the truck, plans and drives the trip |
| `MANAGER` | Logistics manager | books transport (optional: farmers can do it) |

How each is created: sign up in the app with its phone and pick the role (farmer, buyer; the driver
signs up as a driver, see PARALLEL_SESSIONS §10 item 11). The manager is made by Atharv with `backend/scripts/create_staff_user.py`
(see `docs/integration/route-optimizer.md`).

## Getting a token (for each account)

A token is what the phone's login gives the app. Get one the same way the app does, on the `/docs` page,
using the account's real phone (the one-time code arrives by SMS on that phone):

1. Open `https://farmnex-a.fastapicloud.dev/docs` on the laptop.
2. `POST /api/v2/auth/login/request-otp` → *Try it out* → `{"phone_number": "<the account's number>"}` → Execute.
3. The code arrives on that phone. `POST /api/v2/auth/login/verify` → `{"phone_number": "...", "otp": "123456"}` → Execute.
4. The response contains `access_token`. Copy it and paste it straight into your terminal (next section).
   Don't send it in chat or save it in a file. The account must already be signed up in the app (step
   "Accounts" above). The phone number is typed only into the `/docs` page, not saved anywhere.

Repeat for FARMER_1, FARMER_2, BUYER_1, DRIVER (and MANAGER if you made one). If the login asks for more
than these two fields, the `/docs` page shows what it needs.

## Manager account (optional)

The manager books trucks. The simplest way: skip it — the script lets each farmer book their own transport.
To make one, on Atharv's laptop, from `backend/` with the production `DATABASE_URL` in `.env`:

```bash
python scripts/create_staff_user.py <the manager's phone number> --role LOGISTICS_MANAGER
```

It asks you to type `yes`, only ever adds a new user, and then the person logs in with the normal phone
+ code (sign-up isn't needed). Then get a token as above.

## Tokens (once, in your own terminal)

The seed script needs each account's login token. Log each account in on a phone, then get its token
yourself and paste it **into your own terminal** — never into a chat, a file or a screenshot. Tokens last
24 hours, so do this the morning of the demo.

PowerShell (from `backend/`):

```powershell
$env:FARMNEX_TOKEN_FARMER_1 = Read-Host "FARMER_1 token"
$env:FARMNEX_TOKEN_FARMER_2 = Read-Host "FARMER_2 token"
$env:FARMNEX_TOKEN_BUYER    = Read-Host "BUYER_1 token"
$env:FARMNEX_TOKEN_DRIVER   = Read-Host "DRIVER token"
$env:FARMNEX_TOKEN_MANAGER  = Read-Host "MANAGER token"   # optional
```

(`FARMNEX_API_URL` is optional; the default is `https://farmnex-a.fastapicloud.dev`.) Closing the
terminal forgets them.

## Before the demo (warm-up list)

Do these 30–60 minutes before, in this order:

- [ ] **Backend:** open `https://farmnex-a.fastapicloud.dev/health` → `ok`; `/docs` loads.
- [ ] **Forecaster cold start:** open `https://farmnex-ai-forecaster.onrender.com/health` — the first call
      after idle takes about a minute. Open it again until it answers fast.
- [x] **Crop Rescue demo mode:** `CR_ENABLE_SIMULATE=true` on FastAPI Cloud — **done by Atharv (2026-10-03)**.
      Turn it back to `false` after the demo.
- [x] **Route optimizer is on in production** — done (confirmed 2026-10-01: `/docs` lists `/api/v2/routes/...`).
- [x] **`wallet_ledger` RLS line** — done by Atharv (2026-10-03).
- [ ] **Manager account** (optional — without it the farmers book their own transport, and an ADMIN can
      do the same): see "Manager account" below.
- [ ] **Phones:** all six logged in, GPS on for the driver's phone, mobile data/WiFi good, app updated.
- [ ] **Tokens** pasted (above), then check logins only: `python scripts/seed_demo.py --dry-run`
- [ ] **Seed:** `python scripts/seed_demo.py` (re-runnable, makes no duplicates). It makes the truck near
      Pune, both farmers' farms and Tomato listings, the buyer's drop address, one checkout, Pay (demo),
      both orders confirmed, and **pending loads**. So the Pre-bid and Crop Rescue screens are not empty it
      also opens **two pre-bids per farmer** (BUYER_1 bids on each) and **three Crop Rescue lots per farmer**
      (one Tomato lot "At risk", two fresh). Run it on the **demo morning**: rescue lots keep ageing. Unpaid orders expire after 30 minutes, so the script
      pays at once — run it **less than a day** before, not weeks.
- [ ] Each phone: pull to refresh; see the seeded data (FARMER_1 sees the listing, BUYER_1 sees two orders).
- [ ] **One dry run** with `simulate_driver.py` (below) *only if you will do `Reset` afterwards.*

## The demo (5 minutes)

Use the demo crop **Tomato** everywhere. Say what is happening in one sentence per step.

**1. A farmer lists produce (0:00–0:45) — `FARMER_1`**
Tap the **list/sell** action on Home → pick crop *Tomato*, quantity, price per kg → turn on **Pre-bid**
(pre-harvest bidding) → publish. The listing appears on the Market.

**2. Buyers pre-bid (0:45–1:30) — `BUYER_1`, `BUYER_2`**
Market → open the listing → **Open bidding** → each buyer places a bid. (`BUYER_2` bids a little higher.)
`FARMER_1` → **Bids I can see** → **Accept** the best bid. The winner has an order to pay.

**3. Pay (demo) (1:30–2:00) — winner buyer**
Orders → on the order tap **🔒 Pay (demo)** → the wallet shows the money **held** (no real money moves).

**4. Crop Rescue + forecast (2:00–3:00) — `FARMER_1`**
Crop Rescue → **Register a lot** (Tomato, near spoilage) → run the demo **simulate** so the spoilage
alert appears → open the alert: it shows the rescue buyers and the **AI price forecast** for Tomato.

**5. Order confirmed + truck booked (3:00–3:30) — farmer, in `/docs`**
There is no farmer-orders screen. Open `https://farmnex-a.fastapicloud.dev/docs` on the laptop, press
**Authorize** and paste `FARMER_1`'s token (into the page, never into chat):
1. `POST /api/v2/orders/{order_id}/confirm` — the order id comes from `GET /api/v2/orders`.
2. `POST /api/v2/logistics/orders/{order_id}/request-transport` — books a truck (a pending load).

> The seed script already did this for two seeded orders, so the route has loads even if you skip it.
> Doing it live for one order is the "farmer confirms and books" moment.

**6. Pooled route (3:30–4:15) — `DRIVER`**
Logistics → make sure the truck is **online** → **🔎 Find loads near me** or plan the trip → the route
shows both farms as pickups and the buyer as the drop (**pooled**) with the fare → **▶️ Start trip**.
Phone GPS flaky? Run `python scripts/simulate_driver.py --hold-last` (below) — it sends the pings.

**7. Tracking (4:15–4:45) — `BUYER_1`**
Orders → **🚚 Track** → **🗺️ Watch live on map**: the truck moves, with the ETA.

**8. Delivery and payment released (4:45–5:00)**
`DRIVER` completes the last stop (or `simulate_driver.py` without `--hold-last`) → `BUYER_1` taps
**📦 Mark as received** → `FARMER_1` opens **👛 Wallet**: the money moved from *held* to *received*.

## simulate_driver.py (driver's phone fallback)

From `backend/`, with `FARMNEX_TOKEN_DRIVER` set:

```powershell
python scripts/simulate_driver.py --hold-last   # drives and stops before the last drop
python scripts/simulate_driver.py               # finish (or do the whole trip)
```

It puts the truck online, plans the pooled trip if there is none, starts it, sends GPS pings along the
route, and marks each stop done. It prints the live-map link at the end.

## If something goes wrong

| Symptom | Fix |
|---|---|
| Script says a token was refused (401) | The token expired (24 h) — log that account in again and paste a new token |
| "Crop type 'Tomato' not found" | Stop and tell Atharv (crop list, FIX_PLAN F18) |
| Seed: "no map location" / "needs a pickup point" | The farm needs latitude/longitude; the seed farms have it, a hand-made farm may not |
| "Transport needs the weight in kg…" | The listing unit must be kg, quintal or ton |
| Trip planner finds "No pending loads near this vehicle" | The truck base must be within 30 km of the farms (Pune); re-run the seed |
| Forecast screen is slow or empty | Cold start — open the forecaster `/health` and wait a minute |
| Pay says the order expired | Unpaid for 30 min; use `--round` (Reset below) |

## Reset (run the demo again)

Orders and listings can't be deleted, so a new run uses a **new round number**. It makes fresh listings
and a fresh checkout and leaves the old ones behind:

```powershell
python scripts/seed_demo.py --round 2
```

- The first run is round 1. Use 3, 4… for later runs.
- The truck, farms and drop address are reused. If the truck is still `on_trip`, cancel the trip on the
  driver's phone first (or finish it with `simulate_driver.py`).
- `--checkouts 2` makes four loads instead of two (a longer pooled route).
- Old demo listings stay on the Market; tell the audience they are "earlier demo rounds", or ask the
  farmers to close them (delete on the listing closes it).
- Before a **public** demo: `CR_ENABLE_SIMULATE=false` again afterwards.

## What the scripts never do

They call only public `/api/v2` endpoints with the tokens from your terminal. They don't touch the
database, don't print a token, and don't save a token, phone number or key to any file.

Tested against a local fake of the API only (sessions can't log in); the first real run is the
tester's, on the seeded production data — see the S35 dry-run checklist.
