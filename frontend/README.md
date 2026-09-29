# FarmNex — Farmer-to-Buyer Agriculture Marketplace

A Flutter app with a FastAPI backend connecting farmers, buyers, bulk buyers,
logistics partners and APMC administrators.

---

## Read this first — what is and isn't verified

I did not have a Flutter or Python toolchain available while making these
changes, so **nothing here has been compiled, run, or tested on a device.**

| Claim | Status |
|---|---|
| Imports resolve, delimiters balance, every project type imported | verified by static script |
| All 9 languages have all 135 keys, zero gaps | verified by script |
| `flutter pub get` / `analyze` / `test` / `run` | **not run** |
| Backend started, routes or DB tested | **not run** |
| Voice tested on a device in any language | **not possible — see Voice section** |
| Every pre-existing screen fully translated | **partial — see Localization section** |

**Run `flutter analyze` before trusting this build.** Expect a handful of lint
warnings; structural errors should be rare but are possible.

---

## Requirements

| Tool | Version |
|---|---|
| Flutter | 3.27+ (code uses `Color.withValues`, `CardThemeData`) |
| Dart | 3.6+ (records, switch expressions) |
| Android | compileSdk 34, minSdk 21 |
| Xcode | 15+ for iOS |
| Python | 3.10+ for the backend |
| MySQL | 8.0+ |

## Flutter setup

```bash
flutter pub get
flutter analyze
flutter test
flutter run
```

No new Flutter dependencies were added, so `pub get` resolves quickly.

## Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # then edit it
```

`.env` needs at minimum:

```
DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/farmnex
JWT_SECRET=<generate a long random string>
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

Then:

```bash
mysql -u root -p -e "CREATE DATABASE farmnex CHARACTER SET utf8mb4;"
alembic upgrade head                # or: python -m app.db.init_db
uvicorn app.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

**Never commit `.env`.** Secrets stay on the server; the Flutter client must
never hold a payment key secret.

---

## Roles and navigation

Tabs come from one file — `lib/core/navigation/role_tabs.dart`. A role's
screens are never constructed for another role, so there is no route between
workspaces.

| Role | Tabs |
|---|---|
| Farmer | Home / My Crops / Pre-Bid / Crop Rescue / Profile |
| Buyer | Mandi / Crop Rescue / Cart / Orders / Profile |
| Logistics | Loads / Trips / Earnings / Profile |
| Admin | Console / KYC / Users / Money / Profile |
| Guest | Home / Mandi / Crop Rescue / Pre-Bid / Login |

Buyer **My Bids** moved to the Profile screen so Crop Rescue could take a tab
slot without pushing the bar to six items — six cramped items overflow badly
once labels are translated into Tamil or Punjabi.

Wallet is an app-bar action rather than a tab, available to farmer, buyer and
logistics.

### Demo logins

Any password works. The role picker in the login dialog fills these for you.

| Number | Role |
|---|---|
| 9823456789 | Farmer |
| 9800000002 | Buyer |
| 9800000003 | Logistics |
| 9800000004 | Admin |

Signup OTP is `7742` in the mock flow.

> These exist only because the API is not live. `roleHint` and
> `_roleFromDemoMobile()` in `auth_provider.dart` are both marked for deletion
> — the server must be the authority on role.

---

## Crop Rescue — rewritten

Crop Rescue is now a **quick-sale marketplace**. Cold storage, warehouse
management, storage availability and storage booking were **removed entirely**
from this module, along with the old `crop_rescue_dialog.dart`.

**Farmer:** Crop Rescue -> Publish Crop -> pick crop symbol, quantity, **own
price**, location, sell-by date -> Publish. Then edit price/quantity, pause,
resume, delete, and watch sold vs remaining on a progress bar.

**Buyer:** Crop Rescue -> search / filter by category / sort -> crop detail ->
choose quantity -> Buy Now -> Checkout -> Payment -> Order.

Stock only decrements when payment actually succeeds — `recordSale()` is called
from the checkout result, not from the button press.

Files: `lib/models/rescue_listing_model.dart`, `lib/providers/rescue_provider.dart`,
`lib/screens/rescue/{crop_rescue_screen,publish_rescue_sheet,rescue_detail_screen}.dart`

---

## Payments

Architecture was preserved, not replaced.

```
checkout_screen.dart -> payment_provider.dart -> payment_gateway.dart
                                                   |- MockPaymentGateway  (development)
                                                   |- RazorpayGateway     (production stub)
```

**Methods:** UPI, Card, Net Banking, Wallet, Cash on Delivery.
Wallet can be partially applied on top of an online payment.

**Bill:**

| Line | Rate |
|---|---|
| Produce value | price x quantity |
| Platform fee | 1% of goods |
| GST | 5% on the platform fee only |
| Freight | Rs 38/quintal, waived on self-pickup |
| Farmer brokerage | **Rs 0** |

### Development vs production — these are not the same thing

`MockPaymentGateway` is a **simulator**. It moves no money, contacts no bank,
and declines roughly 6% of attempts so the retry UI can be exercised. It is
what ships in the default build.

`RazorpayGateway` is a **stub that does nothing yet.** To go live:

1. `pubspec.yaml` -> `razorpay_flutter: ^1.3.7`
2. Implement `POST /api/payments/create-order` and `POST /api/payments/verify`
3. Wire the success/failure handlers into `RazorpayGateway.charge()`
4. `main.dart` -> `PaymentProvider(gateway: RazorpayGateway())`

**Backend rules, non-negotiable:** the server computes the amount from its own
product and cart records — never from the client. `verify` must check the HMAC
signature before writing the Payment row. Order ownership is validated
server-side. No card data is stored.

### Escrow

```
Placed -> Held -> Transit -> OTP -> Released
```

Money is captured into escrow, not transferred. The logistics partner verifies
the buyer's 4-digit OTP, which calls `PaymentProvider.releaseEscrow()` and
credits the farmer. This is wired for real, not faked in the UI.

**COD does not use escrow** and says so on the checkout sheet. Refunds reverse
the same path through `refundOrder()`.

---

## AI Voice Assistant

**What works today:** the full conversation — slot-filling, multilingual
replies, and real actions.

Farmer, in Marathi:

```
"मला टोमॅटो विकायचे आहेत"   -> "किती किलो टोमॅटो विकायचे आहेत?"
"500 किलो"                  -> "प्रति किलो किती किंमत हवी आहे?"
"25 रुपये"                  -> "500 kg Tomato Rs 25 प्रति kg दराने ठेवू का?"  [होय] [नाही]
होय                          -> a real Crop Rescue listing is created
```

Buyer: *"I need 100 kg onions near Pune"* -> searches Crop Rescue and navigates.
Anyone: *"Open wallet"*, *"Show my orders"*, *"Open Crop Rescue"* -> navigates.

If the farmer says everything at once — *"Sell 500 kg tomato at 25 rupees"* —
the assistant skips straight to confirmation.

Parsing is a deterministic keyword + number parser
(`lib/core/voice/intent_parser.dart`) covering all nine languages, including
Devanagari, Tamil, Bengali, Gurmukhi and Gujarati numerals. It runs offline and
costs nothing. When `/api/ai/chat` is connected, send the raw utterance there
and keep this as the offline fallback.

### The microphone is not enabled

`VoiceService` ships as `TypedVoiceService` — the user types, everything else
behaves identically. Tapping the mic says so plainly rather than faking a
transcript.

To enable real speech, follow the four steps documented in
`lib/core/voice/voice_service.dart`: add `speech_to_text` and `flutter_tts`,
add the Android and iOS permissions, and swap in `PluginVoiceService`.

**A caveat worth planning for:** on-device recognition for Marathi, Punjabi,
Gujarati, Tamil, Bengali, Telugu and Kannada depends on language packs
installed on the handset. Call `SpeechToText.locales()` at startup and fall
back to typed input for anything the device cannot handle. Do not assume all
nine work everywhere — they will not.

---

## Localization

**9 languages, 135 keys each, zero gaps:** English, Hindi, Marathi, Tamil,
Bengali, **Punjabi**, **Gujarati**, Telugu, Kannada.

Punjabi and Gujarati are new. Telugu and Kannada were already present and were
kept rather than dropped.

Use `context.t('key')` from `lib/localization/l10n_extension.dart`. It reads
the provider with `listen: true`, so switching language rebuilds every widget
at once.

### Honest status

All **new** code (Crop Rescue, assistant, strings added this pass) is fully
localized. Some **pre-existing** screens still contain hardcoded English —
notably parts of the admin console, logistics cards, pre-bidding and market.

The keys exist and the mechanism works; what remains is the mechanical job of
replacing literals with `context.t(...)` and adding any new keys to all nine
maps. To find them:

```bash
grep -rn "Text('[A-Z]" lib/screens lib/widgets --include=*.dart
```

Claiming "no mixed languages" today would be false.

---

## Responsive

Cards use `Expanded` / `Flexible` with `maxLines` and `TextOverflow.ellipsis`,
and stat values use `FittedBox`. Bottom navigation is capped at 5 items per
role because translated labels run longer than English.

**Not verified on real devices.** Test on a 5-inch phone in Tamil and Punjabi
first — those produce the longest strings and surface overflow before anything
else does.

---

## Project structure

```
lib/
  core/
    navigation/role_tabs.dart        role -> tabs (access control)
    payments/payment_gateway.dart    gateway interface + adapters
    voice/voice_service.dart         speech abstraction
    voice/intent_parser.dart         multilingual intent + number parsing
    guards/auth_guard.dart
  localization/
    app_translations.dart            9 languages x 135 keys
    l10n_extension.dart              context.t('key')
    language_provider.dart
  models/        payment, rescue_listing, crop, user, deal, buyer
  providers/     auth, payment, cart, listing, rescue, logistics, admin,
                 market, bidding, waste, verification
  screens/       home, market, bidding, rescue, buyer, farmer, logistics,
                 admin, payment, profile, onboarding
  widgets/       symbol_widgets.dart, crop_card.dart, dialogs/
backend/         FastAPI + SQLAlchemy + MySQL
```

## Data flow

```
Flutter UI -> Providers -> Dio -> FastAPI -> Router -> Service/AI -> SQLAlchemy -> MySQL
```

Every provider carries a `TODO BACKEND INTEGRATION` block naming the endpoint
it needs.

---

## Suggested test pass

Once it compiles, in this order:

1. **Payments** — success, failure, retry, wallet, partial wallet + online, COD
2. **Escrow** — buy, logistics accept, pickup, transit, OTP, check farmer wallet
3. **Crop Rescue** — publish, edit price, pause, resume, delete; then buy as a
   buyer and confirm remaining quantity dropped
4. **Voice** — farmer sell flow and buyer search in Marathi and Hindi
5. **Languages** — switch to Punjabi and Tamil, walk every screen, note
   leftover English
6. **Layout** — 5-inch phone, then tablet
