import 'dart:async';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:speech_to_text/speech_recognition_result.dart';
import 'package:speech_to_text/speech_to_text.dart';

abstract class VoiceService {
  bool get supportsSpeech;
  Future<String?> listen(String languageCode);
  Future<void> stopListening();
  Future<void> speak(String text, String languageCode);
  Future<void> stopSpeaking();
}

const Map<String, String> voiceLocales = {
  'en': 'en-IN', 'hi': 'hi-IN', 'mr': 'mr-IN', 'ta': 'ta-IN',
  'bn': 'bn-IN', 'gu': 'gu-IN', 'te': 'te-IN', 'kn': 'kn-IN',
};

String voiceLocaleFor(String languageCode) => voiceLocales[languageCode] ?? 'en-IN';

class PluginVoiceService implements VoiceService {
  final SpeechToText _speech = SpeechToText();
  final FlutterTts _tts = FlutterTts();
  bool _speechReady = false;
  bool _initializing = false;
  Completer<String?>? _listenCompleter;

  @override
  bool get supportsSpeech => true;

  Future<bool> _ensureSpeech() async {
    if (_speechReady) return true;
    if (_initializing) return false;
    _initializing = true;
    try {
      _speechReady = await _speech.initialize(
        onError: (_) {
          if (_listenCompleter != null && !_listenCompleter!.isCompleted) {
            _listenCompleter!.complete(null);
          }
        },
        onStatus: (status) {
          if ((status == 'notListening' || status == 'done') &&
              _listenCompleter != null && !_listenCompleter!.isCompleted) {
            _listenCompleter!.complete(null);
          }
        },
      );
      return _speechReady;
    } finally {
      _initializing = false;
    }
  }

  @override
  Future<String?> listen(String languageCode) async {
    if (!await _ensureSpeech()) return null;
    await stopListening();
    final completer = Completer<String?>();
    _listenCompleter = completer;

    try {
      await _speech.listen(
        localeId: voiceLocaleFor(languageCode),
        listenFor: const Duration(seconds: 12),
        pauseFor: const Duration(seconds: 3),
        partialResults: true,
        cancelOnError: true,
        onResult: (SpeechRecognitionResult result) {
          if (result.finalResult && !completer.isCompleted) {
            completer.complete(result.recognizedWords.trim().isEmpty ? null : result.recognizedWords.trim());
          }
        },
      );
      return await completer.future.timeout(const Duration(seconds: 15), onTimeout: () => null);
    } catch (_) {
      if (!completer.isCompleted) completer.complete(null);
      return completer.future;
    } finally {
      _listenCompleter = null;
      await _speech.stop();
    }
  }

  @override
  Future<void> stopListening() async {
    await _speech.stop();
    if (_listenCompleter != null && !_listenCompleter!.isCompleted) {
      _listenCompleter!.complete(null);
    }
  }

  @override
  Future<void> speak(String text, String languageCode) async {
    try {
      await _tts.setLanguage(voiceLocaleFor(languageCode));
      await _tts.setSpeechRate(0.46);
      await _tts.setVolume(1.0);
      await _tts.speak(text);
    } catch (_) {

    }
  }

  @override
  Future<void> stopSpeaking() async {
    try {
      await _tts.stop();
    } catch (_) {}
  }
}

class TypedVoiceService implements VoiceService {
  @override
  bool get supportsSpeech => false;
  @override
  Future<String?> listen(String languageCode) async => null;
  @override
  Future<void> stopListening() async {}
  @override
  Future<void> speak(String text, String languageCode) async {}
  @override
  Future<void> stopSpeaking() async {}
}
