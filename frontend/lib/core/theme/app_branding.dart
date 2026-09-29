import 'package:flutter/material.dart';
import '../../widgets/auto_translated_text.dart';
import 'app_theme.dart';

class AppBranding {
  static const String appName = 'FarmNex';
  static const String appLogoAsset = 'assets/branding/app_icon.png';
  static const String appLogoFullAsset = 'assets/branding/app_icon_full.png';
}

class FarmNexLogo extends StatelessWidget {
  final double size;
  final BorderRadiusGeometry? borderRadius;
  final List<BoxShadow>? shadows;

  const FarmNexLogo({
    super.key,
    this.size = 64,
    this.borderRadius,
    this.shadows,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        borderRadius: borderRadius ?? BorderRadius.circular(size * 0.28),
        boxShadow: shadows,
      ),
      child: ClipRRect(
        borderRadius: borderRadius ?? BorderRadius.circular(size * 0.28),
        child: Image.asset(
          AppBranding.appLogoAsset,
          fit: BoxFit.cover,

          errorBuilder: (context, error, stackTrace) => Container(
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [AppTheme.primaryGreen, AppTheme.accentTeal],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Icon(Icons.eco, color: Colors.white, size: size * 0.55),
          ),
        ),
      ),
    );
  }
}

class FarmNexWordmark extends StatelessWidget {
  final String tagline;
  final Color textColor;
  final Color taglineColor;

  const FarmNexWordmark({
    super.key,
    required this.tagline,
    this.textColor = Colors.white,
    this.taglineColor = const Color(0xFFDCFCE7),
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        AutoTranslatedText(
          AppBranding.appName.toUpperCase(),
          style: TextStyle(
            fontSize: 28,
            fontWeight: FontWeight.w900,
            letterSpacing: 1.2,
            color: textColor,
          ),
        ),
        const SizedBox(height: 6),
        AutoTranslatedText(
          tagline,
          textAlign: TextAlign.center,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w500,
            color: taglineColor,
          ),
        ),
      ],
    );
  }
}
