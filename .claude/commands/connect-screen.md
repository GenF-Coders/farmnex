---
description: Switch one Flutter provider/screen from demo data to the real backend (e.g. /connect-screen listing)
argument-hint: <provider name, e.g. listing | market | cart | bidding | rescue | logistics | waste>
---

Connect the **$ARGUMENTS** provider (`frontend/lib/providers/$ARGUMENTS_provider.dart`) and its
screens to the real backend. Follow `frontend/CLAUDE.md` → "When connecting a screen to the backend".

1. Find every screen/widget using this provider. List what data each one shows and does.
2. Map each need to a real backend endpoint (read the controllers or `/docs`). Make a table:
   screen need → endpoint → exists? → ownership rules done (FIX_PLAN F1)? If an endpoint is missing or
   not yet safe, stop and tell Atharv what's missing (it may be a FIX_PLAN item or a component).
3. Add URLs to **your feature's section** of `api_config.dart`, typed calls using `ApiClient().dio` in
   your own `lib/core/network/<feature>_api.dart` (not `backend_service.dart`), and plain Dart models with
   `fromJson` (snake_case keys, `public_id` as id).
4. Change the provider to load real data with loading / error / empty states, keeping its public
   getters so screens keep working. Demo data only behind an explicit demo flag, if Atharv wants it.
5. Remove now-dead URLs from `api_config.dart`. Translate new strings.
6. Run `flutter analyze` and `flutter test`. If you can't run the app, write the exact taps Atharv
   should do to test it.
7. Don't edit `docs/FIX_PLAN.md` / `docs/STATUS.md` (the coordinator session does); write
   "Ticks: F13 <provider>", "Doc conflicts:" (docs that disagreed, see `docs/PARALLEL_SESSIONS.md` §4b) and
   "Manual steps:" in the PR description. Commit, push the branch and open a pull request
   unless Atharv said not to.
