# FarmNex status

Short, current picture of where the main app stands. Update this at the end of every task:
tick items in the tables and add one line to the log (newest first).

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
- 2026-09-29 — Proposed (confirm): for the prototype, the route optimizer's `rt_loads` is the delivery
  system and `rt_vehicles` is the vehicle source of truth; core `deliveries` / tracking / proof
  endpoints get unmounted (F1 fast path).

## Open decisions (Atharv)

1. Unmount the unused modules (F1 fast path)? — recommended: yes.
2. Route optimizer's `rt_loads` replaces core `deliveries` for the prototype? — recommended: yes.
3. Live-tracking link works without login (private-link style)? — recommended: yes for the prototype.
4. Pre-bid winner: farmer accepts a bid, or server closes at the end? — recommended: farmer accepts.
5. Voice assistant database: separate free Supabase project? — recommended: yes.

## Log

- 2026-09-29 — Reviewed Farmnex-Voice-Assistant@483599b; voice guide rewritten; crop overlap found
  (only Tomato in all four) → F18; unmount-vs-delete reasoning added to F1; open decisions listed.
- 2026-09-29 — Checked the three component repos; route optimizer guide rewritten from the real repo;
  failure-mode tables added; FINALE_PLAN.md and PROMPTS.md added; F17 added.

- 2026-09-29 — Code review done; Claude Code setup added (CLAUDE.md files, fix plan, integration
  guides, commands).
