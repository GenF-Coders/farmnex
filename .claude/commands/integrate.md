---
description: Plug a component into the main app (crop-rescue | ai-forecaster | route-optimizer | voice-assistant)
argument-hint: <component>
---

Integrate the **$ARGUMENTS** component into this repo.

1. Read `docs/integration/README.md` (shared rules) and `docs/integration/$ARGUMENTS.md`.
2. Check prerequisites and stop to tell Atharv if they're missing:
   - FIX_PLAN **F1–F3** done for any core resource this component reads or writes (always for the
     voice assistant).
   - FIX_PLAN **F17** (`load_dotenv()` first in `main.py`) is done.
   - The component repo is available. If it isn't in this session, ask Atharv to add it (or give the
     path). Read its README / CLAUDE.md / INTEGRATION.md / SPEC at a specific commit, and compare with
     our guide. If they disagree, explain the difference simply and ask which to follow; then update our
     guide.
3. Check the time budget in the guide and `docs/FINALE_PLAN.md`; keep to the simplest version that
   meets the guide's "Done when". Give Atharv a short plan (files you'll add/change, SQL he must run, env vars he must set) and wait
   for OK — he wants to build components together, not have them appear.
4. Put all FarmNex glue in `backend/app/modules/<name>_host.py` (exposing `mount(app)`, and
   `start()`/`stop()` if needed) — `wiring.py` already imports it when the flag is on; don't edit
   `wiring.py` or `main.py`. Work through the **Integration checklist** in `docs/integration/README.md`, one step per commit.
   Never run SQL against the main Supabase database yourself; put it in `backend/migrations/` and
   show Atharv the file to run.
5. Test: `/check`, plus the component's own "Done when" list. Start the backend once with the
   component flag **off** and once **on**; `/docs` must load both times.
6. Ask the `security-reviewer` agent to review the integration diff.
7. Don't edit `docs/STATUS.md` / `docs/FIX_PLAN.md` (the coordinator session does). In the PR
   description write "Ticks:", "Component: <name> @ <source commit hash>" and "Doc conflicts:" (docs that disagreed, see `docs/PARALLEL_SESSIONS.md` §4b), "Manual steps:" (SQL
   files, env vars). Push the branch and open a pull request unless Atharv said not to.
8. Finish with a plain-language summary and a numbered list of what Atharv must do by hand
   (run SQL, set env vars on FastAPI Cloud, deploy the separate service, test on the phone).
