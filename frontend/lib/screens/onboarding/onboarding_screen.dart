import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/storage/storage_service.dart';
import '../../core/theme/app_branding.dart';
import '../../core/theme/app_theme.dart';
import '../../localization/language_provider.dart';
import '../../widgets/dialogs/language_selector_dialog.dart';
import '../main_layout_screen.dart';

class _OnboardPage {
  final IconData icon;
  final Color iconBg;
  final String titleKey;
  final String descKey;

  const _OnboardPage({
    required this.icon,
    required this.iconBg,
    required this.titleKey,
    required this.descKey,
  });
}

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _pageIndex = 0;

  static const _pages = [
    _OnboardPage(
      icon: Icons.handshake_rounded,
      iconBg: AppTheme.primaryGreen,
      titleKey: 'onboard_title_1',
      descKey: 'onboard_desc_1',
    ),
    _OnboardPage(
      icon: Icons.show_chart_rounded,
      iconBg: AppTheme.accentTeal,
      titleKey: 'onboard_title_2',
      descKey: 'onboard_desc_2',
    ),
    _OnboardPage(
      icon: Icons.eco_rounded,
      iconBg: AppTheme.accentAmber,
      titleKey: 'onboard_title_3',
      descKey: 'onboard_desc_3',
    ),
    _OnboardPage(
      icon: Icons.verified_user_rounded,
      iconBg: Color(0xFF0F766E),
      titleKey: 'onboard_title_4',
      descKey: 'onboard_desc_4',
    ),
  ];

  Future<void> _finishOnboarding() async {
    final storage = await StorageService.getInstance();
    await storage.setOnboardingSeen();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const MainLayoutScreen()),
    );
  }

  void _next() {
    if (_pageIndex == _pages.length - 1) {
      _finishOnboarding();
    } else {
      _pageController.nextPage(duration: const Duration(milliseconds: 320), curve: Curves.easeOut);
    }
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();
    final isLastPage = _pageIndex == _pages.length - 1;

    return Scaffold(
      backgroundColor: AppTheme.backgroundWarm,
      body: SafeArea(
        child: Column(
          children: [

            Padding(
              padding: const EdgeInsets.fromLTRB(20, 8, 12, 0),
              child: Row(
                children: [
                  const FarmNexLogo(size: 32, borderRadius: BorderRadius.all(Radius.circular(9))),
                  const SizedBox(width: 8),
                  AutoTranslatedText(
                    'FARMNEX',
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppTheme.textDark, letterSpacing: 0.5),
                  ),
                  const Spacer(),
                  TextButton.icon(
                    onPressed: () => showDialog(context: context, builder: (_) => const LanguageSelectorDialog()),
                    icon: const Icon(Icons.language, size: 16, color: AppTheme.textMuted),
                    label: AutoTranslatedText(
                      lang.currentLanguageOption.nativeName,
                      style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.textMuted),
                    ),
                  ),
                  if (!isLastPage)
                    TextButton(
                      onPressed: _finishOnboarding,
                      child: AutoTranslatedText(
                        lang.translate('onboard_skip'),
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppTheme.textMuted),
                      ),
                    ),
                ],
              ),
            ),

            Expanded(
              child: PageView.builder(
                controller: _pageController,
                itemCount: _pages.length,
                onPageChanged: (i) => setState(() => _pageIndex = i),
                itemBuilder: (context, index) {
                  final page = _pages[index];
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 168,
                          height: 168,
                          decoration: BoxDecoration(
                            color: page.iconBg.withValues(alpha: 0.12),
                            shape: BoxShape.circle,
                          ),
                          child: Center(
                            child: Container(
                              width: 108,
                              height: 108,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  colors: [page.iconBg, page.iconBg.withValues(alpha: 0.75)],
                                  begin: Alignment.topLeft,
                                  end: Alignment.bottomRight,
                                ),
                                shape: BoxShape.circle,
                                boxShadow: [
                                  BoxShadow(color: page.iconBg.withValues(alpha: 0.35), blurRadius: 20, offset: const Offset(0, 10)),
                                ],
                              ),
                              child: Icon(page.icon, color: Colors.white, size: 48),
                            ),
                          ),
                        ),
                        const SizedBox(height: 40),
                        AutoTranslatedText(
                          lang.translate(page.titleKey),
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w900, color: AppTheme.textDark, height: 1.25),
                        ),
                        const SizedBox(height: 14),
                        AutoTranslatedText(
                          lang.translate(page.descKey),
                          textAlign: TextAlign.center,
                          style: const TextStyle(fontSize: 14, color: AppTheme.textMuted, height: 1.5),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),

            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(_pages.length, (i) {
                final isActive = i == _pageIndex;
                return AnimatedContainer(
                  duration: const Duration(milliseconds: 250),
                  margin: const EdgeInsets.symmetric(horizontal: 4),
                  width: isActive ? 22 : 7,
                  height: 7,
                  decoration: BoxDecoration(
                    color: isActive ? AppTheme.primaryGreen : AppTheme.borderLight,
                    borderRadius: BorderRadius.circular(4),
                  ),
                );
              }),
            ),
            const SizedBox(height: 24),

            Padding(
              padding: const EdgeInsets.fromLTRB(24, 0, 24, 20),
              child: SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _next,
                  icon: Icon(isLastPage ? Icons.arrow_forward_rounded : Icons.chevron_right_rounded),
                  label: AutoTranslatedText(
                    isLastPage ? lang.translate('onboard_get_started') : lang.translate('onboard_next'),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
