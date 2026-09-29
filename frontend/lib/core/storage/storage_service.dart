import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const String _accessTokenKey = 'farmnex_access_token';
  static const String _refreshTokenKey = 'farmnex_refresh_token';
  static const String _languageKey = 'farmnex_language_code';
  static const String _languageSelectedKey = 'farmnex_language_selected';
  static const String _userDataKey = 'farmnex_user_data';
  static const String _onboardingSeenKey = 'farmnex_onboarding_seen';

  static StorageService? _instance;
  SharedPreferences? _prefs;

  StorageService._();

  static Future<StorageService> getInstance() async {
    if (_instance == null) {
      _instance = StorageService._();
      _instance!._prefs = await SharedPreferences.getInstance();
    }
    return _instance!;
  }

  Future<void> saveTokens({required String accessToken, required String refreshToken}) async {
    await _prefs?.setString(_accessTokenKey, accessToken);
    await _prefs?.setString(_refreshTokenKey, refreshToken);
  }

  String? getAccessToken() => _prefs?.getString(_accessTokenKey);
  String? getRefreshToken() => _prefs?.getString(_refreshTokenKey);

  Future<void> clearTokens() async {
    await _prefs?.remove(_accessTokenKey);
    await _prefs?.remove(_refreshTokenKey);
    await _prefs?.remove(_userDataKey);
  }

  Future<void> saveLanguage(String langCode) async {
    await _prefs?.setString(_languageKey, langCode);
    await _prefs?.setBool(_languageSelectedKey, true);
  }

  String getLanguage() => _prefs?.getString(_languageKey) ?? 'hi';
  bool hasSelectedLanguage() => _prefs?.getBool(_languageSelectedKey) ?? false;

  Future<void> saveUserData(String jsonString) async => await _prefs?.setString(_userDataKey, jsonString);
  String? getUserData() => _prefs?.getString(_userDataKey);

  bool hasSeenOnboarding() => _prefs?.getBool(_onboardingSeenKey) ?? false;
  Future<void> setOnboardingSeen() async => await _prefs?.setBool(_onboardingSeenKey, true);
}
