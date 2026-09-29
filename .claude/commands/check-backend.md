---
description: Backend checks only (import, pytest, /docs, safety scans) — use after backend changes
---

Run only the backend checks and report in at most 5 short lines (passed / failed / couldn't run and
why). Don't fix anything unless asked. Don't run Flutter.

From `backend/`:
1. `python -c "import app.main"` — the app must import.
2. `python -m pytest -q` — say how many passed / failed / skipped (DB tests skip without `TEST_DATABASE_URL`).
3. `/openapi.json` loads: `uvicorn app.main:app --port 8765 &`, then
   `curl -s -o /dev/null -w "%{http_code}" localhost:8765/openapi.json`, then stop it. If `.env` / JWT
   keys are missing, say so — don't read or create `.env`.
4. Safety scans on changed files (`git diff --name-only origin/main...HEAD`):
   - `DROP `, `TRUNCATE`, or `ALTER TABLE` on a non-prefixed table in `backend/migrations/` → fail;
   - a new route without `get_current_user` (except auth, health, home) → warn;
   - a `*Create`/`*Update` schema with owner ids (`*_by_id`, `buyer_id`, `seller_id`, `payer_id`,
     `bidder_id`, `user_id`) → warn;
   - a dependency added to only one of `pyproject.toml` / `requirements.txt` → warn;
   - a secret-looking string or a `.env` / `.pem` file staged → fail.
