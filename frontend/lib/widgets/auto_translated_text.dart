import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/translation/translation_service.dart';
import '../localization/app_translations.dart';
import '../localization/language_provider.dart';

class AutoTranslatedText extends StatefulWidget {
  final String data;
  final TextStyle? style;
  final StrutStyle? strutStyle;
  final TextAlign? textAlign;
  final TextDirection? textDirection;
  final Locale? locale;
  final bool? softWrap;
  final TextOverflow? overflow;
  final double? textScaleFactor;
  final TextScaler? textScaler;
  final int? maxLines;
  final String? semanticsLabel;
  final TextWidthBasis? textWidthBasis;
  final TextHeightBehavior? textHeightBehavior;
  final Color? selectionColor;

  const AutoTranslatedText(
    this.data, {
    super.key,
    this.style,
    this.strutStyle,
    this.textAlign,
    this.textDirection,
    this.locale,
    this.softWrap,
    this.overflow,
    this.textScaleFactor,
    this.textScaler,
    this.maxLines,
    this.semanticsLabel,
    this.textWidthBasis,
    this.textHeightBehavior,
    this.selectionColor,
  });

  @override
  State<AutoTranslatedText> createState() => _AutoTranslatedTextState();
}

class _AutoTranslatedTextState extends State<AutoTranslatedText> {
  String? _translated;
  String? _language;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final language = context.read<LanguageProvider>().currentLanguage;
    if (_language != language) {
      _language = language;
      _translated = null;
      _translate(widget.data, language);
    }
  }

  @override
  void didUpdateWidget(covariant AutoTranslatedText oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.data != widget.data) {
      final language = context.read<LanguageProvider>().currentLanguage;
      _translated = null;
      _translate(widget.data, language);
    }
  }

  Future<void> _translate(String source, String language) async {
    final bundled = AppTranslations.getBySource(source, language);
    if (bundled != null) {
      if (mounted && _language == language) setState(() => _translated = bundled);
      return;
    }

    if (AppTranslations.containsLocalizedValue(source, language) ||
        (language.toLowerCase() != 'en' && !RegExp(r'[A-Za-z]').hasMatch(source))) {
      if (mounted && _language == language) setState(() => _translated = source);
      return;
    }

    final result = await TranslationService.translate(source, language);
    if (mounted && _language == language) setState(() => _translated = result);
  }

  @override
  Widget build(BuildContext context) {
    final language = context.watch<LanguageProvider>().currentLanguage;
    if (_language != language) {
      _language = language;
      _translated = null;
      _translate(widget.data, language);
    }

    final value = _translated ?? widget.data;
    return Text(
      value,
      style: widget.style,
      strutStyle: widget.strutStyle,
      textAlign: widget.textAlign,
      textDirection: widget.textDirection,
      locale: widget.locale,
      softWrap: widget.softWrap,
      overflow: widget.overflow,
      textScaleFactor: widget.textScaleFactor,
      textScaler: widget.textScaler,
      maxLines: widget.maxLines,
      semanticsLabel: widget.semanticsLabel,
      textWidthBasis: widget.textWidthBasis,
      textHeightBehavior: widget.textHeightBehavior,
      selectionColor: widget.selectionColor,
    );
  }
}
