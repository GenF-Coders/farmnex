# FarmNex — role-based access + payment gateway

Two things changed in this pass: navigation became role-driven, and money became real.

---

## 1. Role-based tabs

Before, `MainLayoutScreen` hard-coded five tabs for everyone. Now every role gets its own
workspace, resolved on each build from the logged-in user.

| Role | Tabs |
|---|---|
| 🧑‍🌾 Farmer | 🏠 Home · 🌾 My Crops · ⏳ Pre-Bid · 🚨 Rescue · 👤 Profile |
| 🏢 Buyer | 🏪 Mandi · 🛒 Cart · 📦 Orders · ⚖️ Bids · 👤 Profile |
| 🚚 Logistics | 📋 Loads · 🚚 Trips · 💰 Earnings · 👤 Profile |
| 🛡️ Admin | 📊 Console · ✅ KYC · 👥 Users · 💳 Money · 👤 Profile |
| 👀 Guest | 🏠 Home · 🏪 Mandi · ⏳ Pre-Bid · 🔐 Login |

**Where it lives:** `lib/core/navigation/role_tabs.dart` is the single source of truth.
Adding or moving a tab is a one-line change there.

**Why it is safe:** tabs are not hidden with `Visibility` — they are never constructed.
A farmer's widget tree contains no cart, so there is no route to one. The app bar follows
the same rule: 🛒 appears only for buyers, 👛 only for roles that hold money, 📋 KYC only
for admins.

**Role changes reset navigation.** Logging in or out lands the user on their first tab,
and the `IndexedStack` is keyed by role so no stale screen survives the switch.

### Login

`AuthProvider.login()` now takes a `roleHint`, and the auth dialog opens with a four-way
symbol picker. Demo numbers, one per workspace:

| Number | Opens |
|---|---|
| `9823456789` | 🧑‍🌾 Farmer |
| `9800000002` | 🏢 Buyer |
| `9800000003` | 🚚 Logistics |
| `9800000004` | 🛡️ Admin |

Password is anything. Admin **self-registration is blocked** — APMC accounts are
provisioned by the board.

> **Before production:** delete `roleHint` and `_roleFromDemoMobile()`. The server is the
> authority on role; trust `user.role` from `POST /api/auth/login`. Both are marked with
> comments in `lib/providers/auth_provider.dart`.

---

## 2. Payment gateway

### Architecture

The app never touches a gateway SDK. It talks to the `PaymentGateway` interface in
`lib/core/payments/payment_gateway.dart`, which has two adapters:

- **`MockPaymentGateway`** — ships in the demo build. Offline, no keys, validates
  instruments and declines ~6% of attempts so the retry path is exercised.
- **`RazorpayGateway`** — production stub with four documented go-live steps
  (add `razorpay_flutter`, add the two FastAPI endpoints, wire the event handlers,
  swap one line in `main.dart`).

### Methods

📲 UPI · 💳 Card · 🏦 Net banking · 👛 Wallet · 💵 Cash on delivery

Each has its own instrument form. The wallet can also be partially applied on top of an
online payment.

### The bill

| Line | Rate |
|---|---|
| 🌾 Produce value | — |
| ⚙️ Platform fee | 1% of goods |
| 🧾 GST | 5% on the fee only |
| 🚚 Freight | ₹38/quintal (waived on self-pickup) |
| 🤝 Farmer brokerage | **₹0** |

### Escrow

```
🧾 placed  ➜  🔒 held  ➜  🚚 transit  ➜  🔐 OTP  ➜  🔓 released
```

Money is captured into escrow, not transferred. It reaches the farmer's wallet only when
the transporter verifies the buyer's 4-digit delivery OTP — that call is wired for real in
`LogisticsActiveScreen`, which invokes `PaymentProvider.releaseEscrow()`. COD orders skip
escrow and say so on the sheet.

Refunds reverse the same path and credit the buyer back.

---

## 3. Symbol-first UI

Built `lib/widgets/symbol_widgets.dart`: stat tiles, action tiles, status pills, section
headers, and a ₹ formatter with Indian lakh/crore grouping (`₹2,45,000`, `₹2.5L`).

Applied throughout — actions are icon squares with tooltips rather than labelled buttons,
statuses are glyphs (🔒 🚚 📦 ✅ ⚠️), the order timeline is symbols only, and tab labels are
one word. 16 new translation keys were added to **all 7 languages**.

---

## New files

```
lib/core/navigation/role_tabs.dart        role → tabs, the access-control surface
lib/core/payments/payment_gateway.dart    gateway interface + mock + Razorpay stub
lib/models/payment_model.dart             methods, statuses, breakdown, orders, ledger
lib/providers/payment_provider.dart       wallet, escrow transitions, orders
lib/providers/cart_provider.dart          🏢 buyer only
lib/providers/listing_provider.dart       🧑‍🌾 farmer only
lib/providers/logistics_provider.dart     🚚 transport only
lib/providers/admin_provider.dart         🛡️ APMC only
lib/screens/payment/checkout_screen.dart  the one payment surface
lib/screens/payment/wallet_screen.dart    balance, top-up, withdraw, ledger
lib/screens/buyer/{cart,buyer_orders,buyer_bids}_screen.dart
lib/screens/farmer/my_crops_screen.dart
lib/screens/logistics/logistics_screens.dart
lib/screens/admin/admin_screens.dart
lib/widgets/symbol_widgets.dart
```

**Removed:** `lib/widgets/dialogs/buy_crop_dialog.dart` — the fake success dialog is
replaced by the real checkout screen.

---

## Before you run it

No new dependencies were added, so this should be quick:

```bash
flutter pub get
flutter analyze
flutter run
```

This code was written without a Flutter toolchain available, so it was verified statically
only (import resolution, delimiter balance, and a check that every project type used is
imported). **Please run `flutter analyze` before trusting it.**

## Backend wiring

Every provider carries a `TODO BACKEND INTEGRATION` block naming its endpoint. The routers
already scaffolded in `backend/app/routers/` (`cart.py`, `products.py`, `deliveries.py`,
`admin.py`) line up with them. Two endpoints still need writing for live payments:

```
POST /api/payments/create-order   → server-side amount, never trust the client
POST /api/payments/verify         → HMAC signature check, writes the Payment row
```

`backend/app/models/payment.py` already has the `Payment`, `Wallet` and
`WalletTransaction` tables these will use, and `lib/models/payment_model.dart` mirrors them
field for field.
