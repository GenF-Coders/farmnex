# AI voice assistant → main app

**Source:** the voice assistant project built on a reusable, provider-agnostic core (`voice_core`:
ports & adapters, an agent turn loop, tool calling, and a confirmation gate for any action that
changes data). It was not part of the 2026-09-29 review — **check this file against that project's
`docs/SPEC.md` / `docs/STATUS.md` before integrating** and update anything that differs.
**What it does:** farmers talk (Marathi / Hindi / English) to ask about prices, rescue alerts,
orders and bids, and to do simple actions ("list 20 quintal onion at ₹2,500") after saying "yes" to a
spoken confirmation.

Follow the shared rules in `README.md` in this folder. This file lists what's specific.

**Status: stretch goal for the 40–50 h build.** Start it only when Crop Rescue, the forecaster and
the P0 security fixes are done. Budget ~8–12 h. **Fallback if time runs out:** demo the voice
service on its own with read-only tools (forecast + rescue alerts) — no write tools, no changes to
the main app beyond F1–F3. Don't start write tools in the last 12 hours before judging.

## Shape

The voice assistant is a **separate service** (streaming audio, speech-to-text, LLM, text-to-speech
don't belong inside the marketplace backend). The FarmNex-specific part lives in its **domain pack**
(`domain_packs/farmnex/`), not in `voice_core`.

```
Flutter mic ──WebSocket + FarmNex access token──► voice service
                                                   ├─ checks the token (FarmNex public key)
                                                   ├─ STT → LLM (+tools) → TTS
                                                   └─ tools call main backend /api/v2/...
                                                        with the SAME user's token
```

## Rules for FarmNex

1. **Login:** the voice service verifies FarmNex access tokens itself using only our **public** key
   (`jwt_public.pem`, RS256, issuer `farmnex-api`, audience `farmnex-mobile`). It never gets the
   private key. `ctx.user_ref = payload["sub"]` (the user's `public_id`).
2. **Tools act as the user:** every tool calls our REST API with the user's own
   `Authorization: Bearer <token>`. That way our ownership and role checks apply to the assistant
   too. **No service/admin key** that could read other users' data. ⇒ **FIX_PLAN F1–F3 must be done
   first**, otherwise the assistant could be talked into reading other people's data.
3. **No user ids in tool schemas** — identity comes from `ctx.user_ref` / the token only.
4. **Writes need confirmation:** create listing, place bid, mark rescue lot sold, cancel order, etc.
   go through the confirmation gate with a per-language template from the pack. Reads run directly.
5. **Token expiry:** access tokens last 15 minutes. The app sends a fresh token (after its normal
   refresh) when (re)connecting or via an auth-update message; the voice service never stores
   refresh tokens. An expired token mid-session → ask the app to refresh, don't fail silently.
6. **Only real endpoints:** each tool maps to an endpoint that exists in `/docs`. Start with the
   components' endpoints (`/api/v2/rescue/*`, `/api/v2/forecast/*`) and core read endpoints; add write
   tools only after F12 gives those endpoints real business rules.
7. **Storage:** keep sessions/transcripts in the voice service's own store. If it must use the main
   Supabase DB, only new `va_` tables via `backend/migrations/04x_va_*.sql`, users as
   `user_public_id`, no FKs. Don't store raw audio unless Atharv decides to (privacy).

## Suggested first tool set (domain pack)

| Tool | Type | Main-backend endpoint |
|---|---|---|
| `get_price_forecast(market, crop, days)` | read | `GET /api/v2/forecast/price` |
| `get_demand(district)` | read | `GET /api/v2/forecast/demand` |
| `list_rescue_alerts()` | read | Crop Rescue alerts endpoint under `/api/v2/rescue/` |
| `get_rescue_matches(lot)` | read | Crop Rescue matches endpoint |
| `list_my_listings()` / `list_my_orders()` | read | `GET /api/v2/product-listings`, `GET /api/v2/orders` (after F1 scopes them to the user) |
| `mark_rescue_lot_sold(lot)` | write → confirm | Crop Rescue mark-sold endpoint |
| `create_listing(crop, qty, unit, price)` | write → confirm | `POST /api/v2/product-listings` (after F1/F2) |

Use exact paths from `/docs` at integration time.

## Main-app changes needed

- None in the backend beyond F1–F3 (+ F7 CORS if the Flutter **web** build talks to the voice
  service). Publish the JWT **public** key to the voice service's config.
- Flutter: `lib/core/voice/voice_service.dart` (on-device `speech_to_text` + `flutter_tts`) and
  `lib/core/voice/intent_parser.dart` exist, plus `lib/widgets/dialogs/ai_assistant_dialog.dart`.
  Decide with Atharv: stream audio to the voice service, keeping on-device speech only as an offline
  fallback. Add a `VoiceAssistantClient` that opens the WebSocket with the current access token from
  `StorageService`, plays TTS audio, and shows the confirmation card with Yes/No buttons as well as
  voice.
- `.env.example` (Flutter side via `api_config.dart`): the voice service URL.

## Done when

- Farmer says (Marathi) "what will onion fetch in Pune tomorrow?" → spoken answer from the forecaster.
- Farmer says "mark my tomato lot sold" → spoken confirmation → "yes" → lot marked sold once
  (a second "yes" doesn't repeat it).
- Asking about another farmer's lots returns nothing (the backend's 404), never someone else's data.
