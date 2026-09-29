# FarmNex language + city + API update

- All standard Flutter `Text(...)` widgets in the frontend have been routed through `AutoTranslatedText` so the selected language can update fixed and dynamic frontend strings.
- Bundled `AppTranslations` are used first; unknown English frontend strings use the translation service.
- Android/iOS use `google_mlkit_translation` through the platform translation service.
- Flutter Web uses the web translation fallback for strings that are not bundled, so dynamic translation on Chrome requires internet access.
- Already-localized strings are protected from being translated a second time.
- Maharashtra city labels are localized for Hindi, Marathi, Telugu, Tamil, Kannada, Bengali and Gujarati while the stored city key remains stable in English.
- The top-right city selector refreshes its visible city label when the language changes.
- The frontend is connected to `https://farmnex.fastapicloud.dev` and uses the explicitly supplied `/health`, `/db`, `/ready`, V2 authentication, users, addresses and farms routes in `lib/core/config/api_config.dart`. No undocumented route has been invented for schemas whose route paths were not included in the supplied documentation excerpt.
- The Home greeting avatar was removed.
- The Fresh Market Home strip remains removed.
