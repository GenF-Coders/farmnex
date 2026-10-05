import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/storage/storage_service.dart';
import '../../core/theme/app_branding.dart';
import '../../core/theme/app_theme.dart';
import '../../localization/language_provider.dart';
import '../main_layout_screen.dart';
import 'onboarding_screen.dart';

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with SingleTickerProviderStateMixin {
  late final AnimationController _controller;
  late final Animation<double> _scale;
  late final Animation<double> _fade;

  static const _minSplashDuration = Duration(milliseconds: 1600);

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
    );
    _scale = Tween<double>(begin: 0.72, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOutBack),
    );
    _fade = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _controller, curve: const Interval(0.0, 0.7, curve: Curves.easeOut)),
    );
    _controller.forward();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    final started = DateTime.now();

    final storage = await StorageService.getInstance();
    final seenOnboarding = storage.hasSeenOnboarding();

    final elapsed = DateTime.now().difference(started);
    final remaining = _minSplashDuration - elapsed;
    if (remaining > Duration.zero) {
      await Future.delayed(remaining);
    }

    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(
        builder: (_) => seenOnboarding ? const MainLayoutScreen() : const OnboardingScreen(),
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>();

    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [AppTheme.primaryGreen, AppTheme.accentTeal],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Column(
            children: [
              const Spacer(flex: 3),
              AnimatedBuilder(
                animation: _controller,
                builder: (context, child) => Opacity(
                  opacity: _fade.value,
                  child: Transform.scale(scale: _scale.value, child: child),
                ),
                child: Column(
                  children: [
                    const FarmNexLogo(
                      size: 108,
                      shadows: [
                        BoxShadow(color: Colors.black26, blurRadius: 24, offset: Offset(0, 10)),
                      ],
                    ),
                    const SizedBox(height: 22),
                    FarmNexWordmark(tagline: lang.translate('tagline')),
                  ],
                ),
              ),
              const Spacer(flex: 4),
              FadeTransition(
                opacity: _fade,
                child: const Padding(
                  padding: EdgeInsets.only(bottom: 36),
                  child: SizedBox(
                    width: 26,
                    height: 26,
                    child: CircularProgressIndicator(
                      strokeWidth: 2.4,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white70),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
