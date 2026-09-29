# FarmNex status

Short, current picture of where the main app stands. Update this at the end of every task:
tick items in the tables and add one line to the log (newest first).

## Fix plan progress (details in FIX_PLAN.md)

| Group | Items | Done |
|---|---|---|
| P0 security | F1 ownership · F2 request fields · F3 roles | 0 / 3 |
| P1 repo health | F4 junk files · F5 deps · F6 /db · F7 CORS · F8 middleware · F9 pooler · F10 entrypoint · F11 tests/CI | 0 / 8 |
| P2 marketplace logic | F12 orders/bids/escrow/payments | 0 / 1 |
| P3 frontend | F13 connect screens · F14 secure tokens · F15 demo names · F16 READMEs | 0 / 4 |

## Components

| Component | Repo state (2026-09-29) | Integrated here? |
|---|---|---|
| Crop Rescue | router module built and tested; Flutter client + INTEGRATION.md (its Phase 5) not done yet | No |
| AI forecaster | service + integration kit ready (written for Supabase Auth — needs changes, see guide) | No |
| Route optimizer | separate repo being built | No |
| Voice assistant | separate `voice_core` project being built | No |

## Decisions log

- 2026-09-29 — Components plug into `backend/app/modules/<name>/` and are mounted under `/api/v2`.
  Component tables use a prefix (`cr_`, `fc_`, `ro_`, `va_`), are created by hand-run SQL in
  `backend/migrations/`, and store the user as `public_id` (UUID text) with no foreign keys to core
  tables.
- 2026-09-29 — Rule: never alter/delete existing tables in the main Supabase DB; only add tables.

## Log

- 2026-09-29 — Code review done; Claude Code setup added (CLAUDE.md files, fix plan, integration
  guides, commands).
