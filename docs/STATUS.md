# FarmNex status

Short, current picture of where the main app stands. Update this at the end of every task:
tick items in the tables and add one line to the log (newest first).

## Fix plan progress (details in FIX_PLAN.md)

| Group | Items | Done |
|---|---|---|
| P0 security | F1 ownership · F2 request fields · F3 roles | 0 / 3 |
| P1 repo health | F4 junk files · F5 deps · F6 /db · F7 CORS · F8 middleware · F9 pooler · F10 entrypoint · F11 tests/CI · F17 load .env | 0 / 9 |
| P2 marketplace logic | F12 orders/bids/escrow/payments | 0 / 1 |
| P3 frontend | F13 connect screens · F14 secure tokens · F15 demo names · F16 READMEs | 0 / 4 |

## Components

| Component | Repo state (2026-09-29) | Integrated here? |
|---|---|---|
| Crop Rescue | `93eec60`: router built and tested; its Phase 5 (Flutter client + INTEGRATION.md) not done | No |
| AI forecaster | `2f6f170`: service + integration kit ready (kit assumes Supabase Auth — adapt per guide) | No |
| Route optimizer | `22d4859` (`farmnex_route_optimization`): package `farmnex_routes` ready; needs host guard, vehicle endpoints, own DB URL | No |
| Voice assistant | repo not reviewed yet — stretch goal | No |

## Decisions log

- 2026-09-29 — Components plug into `backend/app/modules/<name>/` and are mounted under `/api/v2`.
  Component tables use a prefix (`cr_`, `fc_`, `rt_`, `va_`), are created by hand-run SQL in
  `backend/migrations/`, and store the user as `public_id` (UUID text) with no foreign keys to core
  tables.
- 2026-09-29 — Rule: never alter/delete existing tables in the main Supabase DB; only add tables.
- 2026-09-29 — Build window is 40–50 h; scope and order follow `docs/FINALE_PLAN.md`. Voice = stretch.
- 2026-09-29 — Proposed (confirm): for the prototype, the route optimizer's `rt_loads` is the delivery
  system and `rt_vehicles` is the vehicle source of truth; core `deliveries` / tracking / proof
  endpoints get unmounted (F1 fast path).

## Log

- 2026-09-29 — Checked the three component repos; route optimizer guide rewritten from the real repo;
  failure-mode tables added; FINALE_PLAN.md and PROMPTS.md added; F17 added.

- 2026-09-29 — Code review done; Claude Code setup added (CLAUDE.md files, fix plan, integration
  guides, commands).
