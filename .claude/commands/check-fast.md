---
description: Quickest check — only the tests for the files changed in this branch
---

Run the smallest useful check and report in at most 3 lines. Don't fix anything unless asked.

1. `git diff --name-only origin/main...HEAD` — list changed files.
2. Backend files changed → `python -c "import app.main"` (from `backend/`) and only the test files that
   cover the changed modules (`python -m pytest -q tests/<matching files>`).
3. Frontend files changed → `flutter analyze <changed dart files>`.
4. Docs only → nothing to run; say so.

Use this while working. Before opening a PR, run `/check-backend` or `/check-frontend`.
