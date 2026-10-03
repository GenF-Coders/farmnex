import 'package:flutter/material.dart';

class AppTheme {

  static const Color primaryGreen = Color(0xFF178A45);
  static const Color primaryLight = Color(0xFF20A050);
  static const Color accentTeal = Color(0xFF0F766E);
  static const Color accentAmber = Color(0xFFD97706);
  static const Color alertRed = Color(0xFFDC2626);
  static const Color backgroundWarm = Color(0xFFF7F4ED);
  static const Color surfaceWhite = Color(0xFFFFFFFF);
  static const Color textDark = Color(0xFF1C1917);
  static const Color textMuted = Color(0xFF78716C);
  static const Color borderLight = Color(0xFFE7E5E4);

  // Brand accents. Deep leaf green = growth and trust; harvest gold = prosperity and a good
  // season (the colour of ripe grain, marigold and turmeric); warm cream = soil and home.
  static const Color deepGreen = Color(0xFF0E4D2B);
  static const Color harvestGold = Color(0xFFE9A319);
  static const Color goldSoft = Color(0xFFFFF4D6);
  static const Color cream = Color(0xFFFBF8F1);

  /// The signature gradient (morning sun over a field) for hero areas.
  static const LinearGradient brandGradient = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [deepGreen, primaryGreen],
  );

  /// Soft, warm shadow for raised cards (feels touchable without looking heavy).
  static List<BoxShadow> get softShadow => [
        BoxShadow(color: const Color(0xFF3F3A2E).withValues(alpha: .07), blurRadius: 18, offset: const Offset(0, 6)),
      ];

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryGreen,
        primary: primaryGreen,
        secondary: accentAmber,
        error: alertRed,
        surface: surfaceWhite,
        brightness: Brightness.light,
      ),
      scaffoldBackgroundColor: backgroundWarm,
      fontFamily: 'Roboto',
      // Farmers use the app outdoors with one hand: comfortable spacing and full-size tap targets.
      visualDensity: VisualDensity.standard,
      materialTapTargetSize: MaterialTapTargetSize.padded,
      splashFactory: InkSparkle.splashFactory,
      dividerTheme: const DividerThemeData(color: borderLight, thickness: 1, space: 24),
      dialogTheme: DialogThemeData(
        backgroundColor: surfaceWhite,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
        titleTextStyle: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: textDark),
        contentTextStyle: const TextStyle(fontSize: 15, color: textDark, height: 1.4),
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: surfaceWhite,
        surfaceTintColor: Colors.transparent,
        showDragHandle: true,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(24))),
      ),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: textDark,
        contentTextStyle: const TextStyle(fontSize: 15, color: Colors.white, fontWeight: FontWeight.w600),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        insetPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: primaryGreen,
        foregroundColor: Colors.white,
        elevation: 2,
        extendedTextStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: primaryGreen,
          minimumSize: const Size(48, 44),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(color: primaryGreen),
      chipTheme: ChipThemeData(
        showCheckmark: false,
        backgroundColor: surfaceWhite,
        selectedColor: primaryGreen.withValues(alpha: .14),
        side: const BorderSide(color: borderLight),
        shape: const StadiumBorder(),
        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 6),
        labelStyle: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: textDark),
      ),
      listTileTheme: const ListTileThemeData(
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
        titleTextStyle: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: textDark),
        subtitleTextStyle: TextStyle(fontSize: 13.5, color: textMuted),
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: textDark,
        elevation: 1,
        shadowColor: Color(0x22000000),
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontSize: 18,
          fontWeight: FontWeight.w800,
          letterSpacing: -0.3,
          color: primaryGreen,
        ),
      ),
      cardTheme: CardThemeData(
        color: surfaceWhite,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: borderLight, width: 1),
        ),
        margin: EdgeInsets.zero,
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryGreen,
          foregroundColor: Colors.white,
          minimumSize: const Size(double.infinity, 52),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w800,
          ),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: textDark,
          minimumSize: const Size(double.infinity, 52),
          side: const BorderSide(color: borderLight, width: 1.2),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          textStyle: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: borderLight),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: borderLight),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: primaryGreen, width: 1.8),
        ),
        labelStyle: const TextStyle(color: textMuted, fontSize: 15),
        hintStyle: const TextStyle(color: Color(0xFFA8A29E), fontSize: 15),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: Colors.white,
        selectedItemColor: primaryGreen,
        unselectedItemColor: textMuted,
        selectedLabelStyle: TextStyle(fontWeight: FontWeight.w700, fontSize: 11),
        unselectedLabelStyle: TextStyle(fontWeight: FontWeight.w500, fontSize: 11),
        elevation: 8,
        type: BottomNavigationBarType.fixed,
      ),
    );
  }
}
