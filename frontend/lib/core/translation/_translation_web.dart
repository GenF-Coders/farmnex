import 'dart:convert';
import 'package:http/http.dart' as http;

final Map<String, String> _webTranslationCache = <String, String>{};

String _normalize(String text) => text.replaceAll(RegExp(r'\\s+'), ' ').trim();

Future<String> translateTextPlatform(String text, String targetLanguage) async {
  if (text.trim().isEmpty || targetLanguage.toLowerCase() == 'en') return text;

  final source = _normalize(text);
  if (source.isEmpty || !RegExp(r'[A-Za-z]').hasMatch(source)) return text;

  final key = '$targetLanguage|$source';
  final cached = _webTranslationCache[key];
  if (cached != null && cached.isNotEmpty) return cached;

  try {
    final uri = Uri.https('translate.googleapis.com', '/translate_a/single', {
      'client': 'gtx',
      'sl': 'auto',
      'tl': targetLanguage.toLowerCase(),
      'dt': 't',
      'q': source,
    });
    final response = await http.get(uri).timeout(const Duration(seconds: 8));
    if (response.statusCode != 200) return text;
    final decoded = jsonDecode(response.body);
    final parts = decoded is List && decoded.isNotEmpty ? decoded[0] : null;
    if (parts is! List) return text;
    final translated = parts
        .whereType<List>()
        .map((part) => part.isNotEmpty ? part[0]?.toString() ?? '' : '')
        .join();
    if (translated.trim().isEmpty) return text;
    _webTranslationCache[key] = translated;
    return translated;
  } catch (_) {
    return text;
  }
}
