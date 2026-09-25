import 'package:flutter/widgets.dart';
import 'package:provider/provider.dart';

import 'app_translations.dart';
import 'language_provider.dart';

extension L10nContext on BuildContext {
  String t(String key) {
    final language = Provider.of<LanguageProvider>(this).currentLanguage;
    return AppTranslations.get(key, language);
  }

  String tf(String key, List<String> args) {
    var value = t(key);
    for (final arg in args) {
      value = value.replaceFirst('{}', arg);
    }
    return value;
  }

  String get languageCode =>
      Provider.of<LanguageProvider>(this, listen: false).currentLanguage;
}
