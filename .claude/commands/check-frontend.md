---
description: Flutter checks only (analyze, test, Dio usage) — use after frontend changes
---

Run only the Flutter checks and report in at most 5 short lines. Don't fix anything unless asked.
Don't run backend checks.

From `frontend/` (if Flutter isn't installed, say so and stop):
1. `flutter analyze` — count new issues in the files you changed (ignore issues that already existed on `main`).
2. `flutter test`.
3. `grep -rn "http://\|Dio()" lib` outside `api_client.dart` → warn (use `ApiClient().dio`).
