---
description: Work on one item from docs/FIX_PLAN.md (e.g. /fix F1 payment)
argument-hint: <F-number> [module]
---

Fix item **$ARGUMENTS** from `docs/FIX_PLAN.md`.

1. Read the item in `docs/FIX_PLAN.md`, plus `CLAUDE.md` and `backend/CLAUDE.md` or
   `frontend/CLAUDE.md` for the area it touches. If the item is large (F1, F2, F12, F13) and no module
   was given, list the sub-steps and do only the **first** one this run.
2. Tell Atharv in 2–4 plain sentences what you will change and why. If the item says
   "ask Atharv" or involves a business decision (who may do what, money rules), ask first and wait.
3. Make the change. Follow the existing layering and the ownership pattern
   (`services/farm_crop_service.py`). Never alter existing database tables.
4. Add or update tests exactly as the item's **How to check** says. Run `/check`.
5. For auth / ownership / payment / bid changes: ask the `security-reviewer` agent to review the diff
   and fix what it finds.
6. Don't edit `docs/FIX_PLAN.md` or `docs/STATUS.md` (several sessions run in parallel; the
   coordinator session updates them — see `docs/PARALLEL_SESSIONS.md`). Instead, put
   "Ticks: <items done>" and "Doc conflicts:" (docs that disagreed, see `docs/PARALLEL_SESSIONS.md` §4b), "Manual steps: <SQL / env vars / none>" in the PR description.
7. Commit with a clear message (`fix(F1): ownership checks for payments`). Push the branch and
   open a pull request unless Atharv said not to.
8. Finish with a short plain-language summary: what changed, how you checked it, and anything Atharv
   must do by hand.
