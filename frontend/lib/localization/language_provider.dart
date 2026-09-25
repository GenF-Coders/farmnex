import 'package:flutter/material.dart';
import '../core/storage/storage_service.dart';
import 'app_translations.dart';

class LanguageProvider extends ChangeNotifier {
  String _currentLanguage = 'hi';
  StorageService? _storage;

  String get currentLanguage => _currentLanguage;

  LanguageOption get currentLanguageOption {
    return AppTranslations.supportedLanguages.firstWhere(
      (lang) => lang.code == _currentLanguage,
      orElse: () => AppTranslations.supportedLanguages[0],
    );
  }

  LanguageProvider() {
    _loadLanguage();
  }

  Future<void> _loadLanguage() async {
    _storage = await StorageService.getInstance();
    final saved = _storage?.getLanguage();
    _currentLanguage = AppTranslations.supportedLanguages.any((l) => l.code == saved)
        ? saved!
        : 'hi';
    notifyListeners();
  }

  Future<void> setLanguage(String code) async {
    if (_currentLanguage == code) return;
    _currentLanguage = code;
    _storage ??= await StorageService.getInstance();
    await _storage?.saveLanguage(code);
    notifyListeners();
  }

  String translate(String key) {
    return AppTranslations.get(key, _currentLanguage);
  }
}
