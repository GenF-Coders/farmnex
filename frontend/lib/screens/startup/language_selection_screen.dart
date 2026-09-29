import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../localization/app_translations.dart';
import '../../localization/language_provider.dart';
import '../main_layout_screen.dart';

class LanguageSelectionScreen extends StatefulWidget {
  const LanguageSelectionScreen({super.key});
  @override State<LanguageSelectionScreen> createState() => _LanguageSelectionScreenState();
}

class _LanguageSelectionScreenState extends State<LanguageSelectionScreen> {
  bool _busy = false;
  Future<void> _choose(String code) async {
    if (_busy) return;
    setState(() => _busy = true);
    await context.read<LanguageProvider>().setLanguage(code);
    if (!mounted) return;
    Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const MainLayoutScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFEEF1EA),
      body: SafeArea(child: Center(child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 720), child: Container(
        color: const Color(0xFFF7F6F2),
        padding: const EdgeInsets.fromLTRB(26, 34, 26, 22),
        child: Column(children: [
          const Icon(Icons.eco_rounded, color: AppTheme.primaryGreen, size: 42),
          const SizedBox(height: 6),
          AutoTranslatedText('FarmNex', style: TextStyle(fontSize: 25, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
          const SizedBox(height: 5),
          AutoTranslatedText('With Farmers For a Better Tomorrow', textAlign: TextAlign.center, style: TextStyle(fontSize: 12.5, color: AppTheme.textMuted)),
          const SizedBox(height: 18),
          ClipRRect(borderRadius: BorderRadius.circular(16), child: Image.asset('assets/html_reference/60a85882-b310-41b8-add3-f48c3e9e550a.webp', width: double.infinity, height: 220, fit: BoxFit.cover, filterQuality: FilterQuality.high)),
          const SizedBox(height: 19),
          const Align(alignment: Alignment.centerLeft, child: AutoTranslatedText('SELECT YOUR LANGUAGE', style: TextStyle(fontSize: 10, letterSpacing: .7, fontWeight: FontWeight.w800, color: Color(0xFF9CA3AF)))),
          const SizedBox(height: 8),
          Expanded(child: Consumer<LanguageProvider>(builder: (_, provider, __) => ListView.separated(
            itemCount: AppTranslations.supportedLanguages.length,
            separatorBuilder: (_, __) => const SizedBox(height: 7),
            itemBuilder: (_, i) {
              final l = AppTranslations.supportedLanguages[i];
              final selected = provider.currentLanguage == l.code;
              return InkWell(onTap: () => _choose(l.code), borderRadius: BorderRadius.circular(11), child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                decoration: BoxDecoration(color: selected ? AppTheme.primaryGreen : Colors.white, borderRadius: BorderRadius.circular(11), border: Border.all(color: selected ? AppTheme.primaryGreen : const Color(0xFFE2E0D8))),
                child: Row(children: [Expanded(child: AutoTranslatedText(l.nativeName, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: selected ? Colors.white : const Color(0xFF1A1A1A)))), AutoTranslatedText(l.name, style: TextStyle(fontSize: 10, color: selected ? Colors.white70 : AppTheme.textMuted)), const SizedBox(width: 7), Icon(selected ? Icons.check_circle_rounded : Icons.arrow_forward_ios_rounded, size: 15, color: selected ? Colors.white : AppTheme.primaryGreen)],),
              ));
            },
          ))),
          if (_busy) const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2)),
        ]),
      )))),
    );
  }
}
