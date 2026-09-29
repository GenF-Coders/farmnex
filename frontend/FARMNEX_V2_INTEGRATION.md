# FarmNex + FarmNex FastAPI V2 integration

This build uses the **FarmNex complete UI project as the UI source of truth** and the supplied FarmNex V2 Flutter integration as the API/network source of truth.

## Startup

1. First launch opens **Language Selection**.
2. Selecting a language saves it locally and routes directly to the existing FarmNex Home screen.
3. The language can still be changed from the top bar.

## FarmNex base URL

`https://farmnex.fastapicloud.dev`

The V2 paths implemented in `lib/core/config/api_config.dart` and `lib/core/network/backend_service.dart` are the paths from the supplied Swagger contract:

- System: `/health`, `/db`, `/ready`
- Authentication: V2 OTP register/login, refresh, logout
- Users: `/api/v2/users`, `/api/v2/users/me`, profile image
- Addresses: list/create/get/update/delete/default/activate/deactivate
- Farms: create/list/get/update/delete and farm file upload/get/delete/download

`ApiClient` adds the stored Bearer token automatically and attempts access-token refresh after a 401.

## Translation

`lib/core/translation/translation_service.dart` exposes the requested static utility:

```dart
await TranslationService.translate('Hello', 'mr');
await TranslationService.translateContent(apiResponse, 'mr');
```

The native implementation uses `google_mlkit_translation` for English -> selected language. The web implementation safely falls back to the original text because Google ML Kit Translation is a native Flutter plugin. UI labels continue to use the existing FarmNex translations.

`ApiClient.getTranslated()` and `postTranslated()` are available for human-readable API payloads. They do **not** automatically mutate normal model responses, because translating IDs, roles, URLs, tokens or machine fields would corrupt API data.

## AI voice agent

The existing FarmNex AI assistant is retained and now uses `PluginVoiceService` with:

- `speech_to_text` for microphone input
- `flutter_tts` for spoken responses
- existing multilingual intent parser for crop, quantity, price and navigation commands

Android and iOS microphone/speech permissions are included.

## Uploads

The existing UI now includes a role-aware Upload Center.

### Farmer
Crop photo/video selection is available. The only file-upload endpoint present in the supplied V2 Swagger is:

`POST /api/v2/farms/{farm_public_id}/file`

Therefore the UI asks for the Farm public ID and sends the selected file to that documented endpoint rather than inventing a crop-media API.

### Buyer / Logistics
Document selection is available for PDF/JPG/PNG/DOC/DOCX. The supplied V2 API model does **not** expose a buyer/logistics document-upload endpoint, so the UI does not send those files to an unrelated route. Once FarmNex provides that endpoint, it can be wired into the Upload Center without changing the UI flow.

## Pull to refresh

The complete FarmNex UI's existing Home `RefreshIndicator` is preserved. Existing screens and role workspaces are otherwise kept intact.

## Authentication UI

The old demo password flow has been replaced with the supplied FarmNex V2 OTP flow while keeping the original FarmNex role-first visual design:

`Request OTP -> Verify OTP -> token session -> profile update (registration)`

No mock JWT or fake OTP is used by the authentication dialog.

## Run

```powershell
flutter clean
flutter pub get
flutter analyze
flutter run -d chrome
```

For Android/iOS, microphone permissions are already included. On Chrome, microphone access requires browser permission and localhost/HTTPS.
