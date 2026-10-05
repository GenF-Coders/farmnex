import '_translation_platform.dart';

class TranslationService {
  const TranslationService._();

  static Future<String> translate(String text, String targetLanguage) {
    return translateTextPlatform(text, targetLanguage);
  }

  static Future<dynamic> translateContent(dynamic content, String targetLanguage) async {
    if (content is String) return translate(content, targetLanguage);
    if (content is List) {
      final result = <dynamic>[];
      for (final value in content) {
        result.add(await translateContent(value, targetLanguage));
      }
      return result;
    }
    if (content is Map) {
      final result = <dynamic, dynamic>{};
      for (final entry in content.entries) {

        result[entry.key] = await translateContent(entry.value, targetLanguage);
      }
      return result;
    }
    return content;
  }
}
