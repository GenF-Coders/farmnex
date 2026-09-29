# FarmNex — FarmNex V2 integrated

This build uses the FarmNex UI as the UI source of truth and the supplied FarmNex FastAPI V2 contract for backend integration.

## Supported app languages
English, Hindi, Marathi, Telugu, Tamil, Kannada, Bengali, Gujarati.

Punjabi has intentionally been removed from the app language list, locale list, voice locale map, and AI assistant language map.

## First launch
The app opens on language selection. After selection it opens the existing FarmNex home layout.

## Run
```powershell
flutter clean
flutter pub get
flutter analyze
flutter run -d chrome
```

Google ML Kit Translation is used by `TranslationService` on supported native platforms. Chrome uses the safe web implementation because ML Kit Translation is a native plugin.


## Latest UI / Flow updates
- App launch always opens the language-selection screen first. The previously selected language remains available as the saved default, and Continue takes the user directly to Home.
- AI Voice Assistant is available from the Home hero and app bar for every role.
- Farmers have a dedicated Upload Center flow for crop photos and videos.
- Buyers, Logistics and Admin users get document/verification uploads.
- Payments default to a deterministic **Razorpay Test Mode (Sandbox)** adapter. It does not charge real money and requires no secret key. Production Razorpay should use server-created Orders and server-side signature verification.

## Latest UI flow changes
- App opens on language selection; tapping a language immediately opens Home.
- The global top upload shortcut is removed. KYC document upload is available only inside the logged-in user's KYC tab.
- KYC is role-scoped: Farmer, Buyer, Logistics and Admin accounts only see their own KYC area. Farmer and Buyer can select Aadhaar Card in addition to their role documents.
- Farmer crop photo/video upload is available on the individual crop cards in My Crops, Market, Pre-Bid and Crop Rescue; Buyer market cards show uploaded crop media.
- Buyer Profile > My Bids shows bids recorded for the logged-in buyer.
- Registration includes Name, Surname, Date of birth and Gender in addition to the existing fields.
- Removed technical backend/API wording from user-facing screens.
