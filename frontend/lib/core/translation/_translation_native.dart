import 'package:google_mlkit_translation/google_mlkit_translation.dart';

TranslateLanguage? _language(String code) {
  switch (code.toLowerCase()) {
    case 'hi': return TranslateLanguage.hindi;
    case 'mr': return TranslateLanguage.marathi;
    case 'ta': return TranslateLanguage.tamil;
    case 'bn': return TranslateLanguage.bengali;
    case 'gu': return TranslateLanguage.gujarati;
    case 'te': return TranslateLanguage.telugu;
    case 'kn': return TranslateLanguage.kannada;
    case 'en':
    default: return TranslateLanguage.english;
  }
}

Future<String> translateTextPlatform(String text, String targetLanguage) async {
  if (text.trim().isEmpty || targetLanguage.toLowerCase() == 'en') return text;
  final language = _language(targetLanguage);
  if (language == null) return text;

  final translator = OnDeviceTranslator(
    sourceLanguage: TranslateLanguage.english,
    targetLanguage: language,
  );
  try {
    return await translator.translateText(text);
  } finally {
    await translator.close();
  }
}
