# FarmNex Flutter — HTML Reference UI Rebuild

This build recreates the supplied FarmNex standalone HTML reference as a native Flutter UI layer while retaining the existing FarmNex/FarmNex functional stack.

## Preserved functionality
- FastAPI V2 OTP registration/login, JWT refresh and logout
- Four roles: Farmer, Buyer, Logistics, Admin
- Role-scoped navigation and profile/KYC flows
- Farmer crop listings, crop media upload and pre-harvest bidding
- Buyer marketplace, cart, orders and My Bids
- Crop Rescue and Waste to Wealth flows
- Logistics loads, active trips and earnings
- Admin console, users, KYC and payments
- Razorpay-compatible test/sandbox payment flow already present in the project
- AI assistant, voice controls and AI forecast dialogs
- Pull-to-refresh on scrollable home surfaces
- Google ML Kit Translation integration through the existing static TranslationService
- No Punjabi language option in the application UI

## UI reference conversion
The visual layer is rebuilt around the supplied HTML reference dimensions and visual language:
- 411 x 843 mobile composition
- off-white page background
- FarmNex green primary color
- Manrope-style compact typography
- rounded white cards and compact icon navigation
- reference hero/crop/avatar assets extracted from the supplied HTML bundle

## Important
The assistant environment used for this archive did not have the Flutter SDK installed, so a local `flutter analyze`/`flutter build` could not be executed here. The archive itself is checked for ZIP integrity. Run `flutter pub get` followed by `flutter analyze` and your normal platform build locally.
