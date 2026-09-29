import 'package:flutter_secure_storage/flutter_secure_storage.dart';
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
  final FlutterSecureStorage _secure = const FlutterSecureStorage();

  // Tokens live in secure storage; a copy is kept in memory so the getters stay synchronous.
  String? _accessToken;
  String? _refreshToken;

  StorageService._();

  static Future<StorageService> getInstance() async {
    if (_instance == null) {
      final service = StorageService._();
      service._prefs = await SharedPreferences.getInstance();
      await service._loadTokens();
      _instance = service;
    }
    return _instance!;
  }

  Future<void> _loadTokens() async {
    try {
      _accessToken = await _secure.read(key: _accessTokenKey);
      _refreshToken = await _secure.read(key: _refreshTokenKey);
    } catch (_) {
      // Secure storage unavailable: treat as logged out.
    }

    // One-time migration: move tokens from the old shared_preferences keys, then delete them.
    final oldAccess = _prefs?.getString(_accessTokenKey);
    final oldRefresh = _prefs?.getString(_refreshTokenKey);
    if (oldAccess != null || oldRefresh != null) {
      if ((_accessToken ?? '').isEmpty && oldAccess != null && oldRefresh != null) {
        await saveTokens(accessToken: oldAccess, refreshToken: oldRefresh);
      }
      await _prefs?.remove(_accessTokenKey);
      await _prefs?.remove(_refreshTokenKey);
    }
  }

  Future<void> saveTokens({required String accessToken, required String refreshToken}) async {
    _accessToken = accessToken;
    _refreshToken = refreshToken;
    await _secure.write(key: _accessTokenKey, value: accessToken);
    await _secure.write(key: _refreshTokenKey, value: refreshToken);
  }

  String? getAccessToken() => _accessToken;
  String? getRefreshToken() => _refreshToken;

  Future<void> clearTokens() async {
    _accessToken = null;
    _refreshToken = null;
    try {
      await _secure.delete(key: _accessTokenKey);
      await _secure.delete(key: _refreshTokenKey);
    } catch (_) {}
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
