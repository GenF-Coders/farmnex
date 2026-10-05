---
description: Full check of the whole repo (backend + frontend) — for the coordinator after a wave, not for every task
---

Full check — use after a wave or before a demo. For one task use `/check-backend`,
`/check-frontend` or `/check-fast` instead (they're cheaper and faster).

Run the checks and report results simply (what passed, what failed, what couldn't run and why).
Don't fix anything unless asked — just report and suggest the next step.

Backend (from `backend/`):
1. `python -c "import app.main"` — the app must import.
2. `python -m pytest -q` — tests (DB tests skip without `TEST_DATABASE_URL`; say how many skipped).
3. Start briefly and confirm `/docs` and `/openapi.json` load:
   `uvicorn app.main:app --port 8765 &` then `curl -s -o /dev/null -w "%{http_code}" localhost:8765/openapi.json`, then stop it.
   (Needs a `.env` with `DATABASE_URL` and JWT keys; if missing, say so — don't read or create `.env`.)
4. Quick safety scans on changed files (`git diff --name-only main...HEAD`):
   - any `DROP `, `TRUNCATE`, `ALTER TABLE` on a non-prefixed table in `backend/migrations/` → fail;
   - any new route without `get_current_user` (except auth, health, home) → warn;
   - any `*Create`/`*Update` schema with owner ids (`*_by_id`, `buyer_id`, `seller_id`, `payer_id`,
     `bidder_id`, `user_id`) → warn;
   - any secret-looking string or `.env` / `.pem` file staged → fail.

Frontend (from `frontend/`, only if Flutter is installed):
5. `flutter analyze` and `flutter test`.
6. `grep -rn "http://\|Dio()" lib` outside `api_client.dart` → warn (should use `ApiClient().dio`).
