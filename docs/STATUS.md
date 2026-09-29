# FarmNex status

Short, current picture of where the main app stands. **Only the coordinator session edits this file**
(see `docs/PARALLEL_SESSIONS.md`); other sessions put "Ticks:" / "Manual steps:" in their PR description.

## Fix plan progress (details in FIX_PLAN.md)

| Group | Items | Done |
|---|---|---|
| P0 security | F1 ownership · F2 request fields · F3 roles | 0 / 3 |
| P1 repo health | F4 junk files · F5 deps · F6 /db · F7 CORS · F8 middleware · F9 pooler · F10 entrypoint · F11 tests/CI · F17 load .env · F18 crop list | 0 / 10 |
| P2 marketplace logic | F12 orders/bids/escrow/payments | 0 / 1 |
| P3 frontend | F13 connect screens · F14 secure tokens · F15 demo names · F16 READMEs | 0 / 4 |

## Components

| Component | Repo state (2026-09-29) | Integrated here? |
|---|---|---|
| Crop Rescue | `6f90439`: router built and tested; **Phase 5 (Flutter client + INTEGRATION.md) still not done** | No |
| AI forecaster | `2f6f170`: service + integration kit ready (kit assumes Supabase Auth — adapt per guide) | No |
| Route optimizer | `307e954` (`farmnex_route_optimization`): package `farmnex_routes` ready; needs host guard, vehicle endpoints, own DB URL | No |
| Voice assistant | `483599b` (`Farmnex-Voice-Assistant`): M4 done (speech, agent, confirmations); **login adapter, real tools, Flutter client missing** — stretch goal | No |

## Decisions log

- 2026-09-29 — Components plug into `backend/app/modules/<name>/` and are mounted under `/api/v2`.
  Component tables use a prefix (`cr_`, `fc_`, `rt_`, `va_`), are created by hand-run SQL in
  `backend/migrations/`, and store the user as `public_id` (UUID text) with no foreign keys to core
  tables.
- 2026-09-29 — Rule: never alter/delete existing tables in the main Supabase DB; only add tables.
- 2026-09-29 — Demo story uses Tomato (only crop supported everywhere).
- 2026-09-29 — Build window is 40–50 h; scope and order follow `docs/FINALE_PLAN.md`. Voice = stretch.
- 2026-09-29 — **Confirmed by Atharv:** (1) unmount the 9 unused modules (F1 fast path);
  (2) the route optimizer's `rt_loads` replaces core `deliveries` and `rt_vehicles` is the vehicle
  source of truth; (3) the live-tracking link works without login (private-link style) for the
  prototype; (4) pre-bid winner: the **farmer accepts** a bid; (5) the voice assistant uses a
  separate free Supabase project.
- 2026-09-29 — Work runs as parallel Claude Code sessions per `docs/PARALLEL_SESSIONS.md`; only the
  coordinator session edits this file and `FIX_PLAN.md`.

## Verified facts (the single source — other docs link here)

| Fact | Value | Source / checked |
|---|---|---|
| Production dependency file | FastAPI Cloud installs from `backend/pyproject.toml` when it exists; `requirements.txt` only if there's no pyproject. Keep both in sync. | fastapicloud.com docs "Install Dependencies", 2026-09-29 |
| Deploys | With FastAPI Cloud's GitHub integration, every push to the default branch (`main`) deploys; no PR previews. **Unconfirmed:** whether this project has GitHub connected, and that it deploys from `backend/`. | fastapicloud.com docs "GitHub Integration", 2026-09-29 |
| Entrypoint | FastAPI Cloud auto-detects `app/main.py` (`app.main:app`). | fastapicloud.com docs "Migrate an Existing Project" |
| Crop-name map | `backend/app/modules/crops.py` | decision 2026-09-29 |
| Main crop names | `crop_types.name`, capitalised (`Tomato`, `Onion`, …) | `app/main.py` DEFAULT_CROP_TYPES |
| Crop Rescue crop codes | lowercase: tomato, spinach, okra, brinjal, cauliflower, grapes, capsicum, cucumber | `farmnex_crop_rescue` `crop_rescue/data/crops.json` @ 6f90439 |
| Forecaster crops | `Onion`, `Tomato`, `Potato` (exact case) | `farmnex_ai_forecaster` `config.yaml` @ 2f6f170 |
| Voice crop ids | lowercase (`tomato`, `onion`, `potato`, + Crop Rescue codes after its FARMNEX_HOST change 3) | voice repo `docs/FARMNEX_HOST.md` |
| User id given to components | `str(user.public_id)` (UUID string) | decision |
| Component host files | `app/modules/<name>_host.py`, loaded by `app/modules/wiring.py` via its `ENABLE_*` flag | PARALLEL_SESSIONS §7 |
| `wallet_ledger` | new core model, created by the startup `create_all` (no SQL file) | FIX_PLAN F12 |
| Public sign-up roles today | FARMER, BUYER, VENDOR (`public_registration_roles`, env-overridable) | `app/core/config.py` |

## Waiting for Atharv (manual steps from merged PRs)

- Confirm in the FastAPI Cloud dashboard: is GitHub connected (auto-deploy on merge to `main`)? Does it deploy from the `backend/` folder?

## Log

- 2026-09-29 — Reviewed Farmnex-Voice-Assistant@483599b; voice guide rewritten; crop overlap found
  (only Tomato in all four) → F18; unmount-vs-delete reasoning added to F1; open decisions listed.
- 2026-09-29 — Checked the three component repos; route optimizer guide rewritten from the real repo;
  failure-mode tables added; FINALE_PLAN.md and PROMPTS.md added; F17 added.

- 2026-09-29 — Code review done; Claude Code setup added (CLAUDE.md files, fix plan, integration
  guides, commands).
