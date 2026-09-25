import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'core/theme/app_theme.dart';
import 'localization/language_provider.dart';
import 'providers/admin_provider.dart';
import 'providers/auth_provider.dart';
import 'providers/bidding_provider.dart';
import 'providers/cart_provider.dart';
import 'providers/crop_media_provider.dart';
import 'providers/listing_provider.dart';
import 'providers/logistics_provider.dart';
import 'providers/payment_provider.dart';
import 'providers/market_provider.dart';
import 'providers/rescue_provider.dart';
import 'providers/verification_provider.dart';
import 'providers/waste_provider.dart';
import 'screens/startup/startup_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => LanguageProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => MarketProvider()),
        ChangeNotifierProvider(create: (_) => BiddingProvider()),
        ChangeNotifierProvider(create: (_) => RescueProvider()),
        ChangeNotifierProvider(create: (_) => WasteProvider()),
        ChangeNotifierProvider(create: (_) => VerificationProvider()),
        ChangeNotifierProvider(create: (_) => CropMediaProvider()),

        ChangeNotifierProvider(create: (_) => CartProvider()),
        ChangeNotifierProvider(create: (_) => ListingProvider()),
        ChangeNotifierProvider(create: (_) => LogisticsProvider()),
        ChangeNotifierProvider(create: (_) => AdminProvider()),

        ChangeNotifierProvider(create: (_) => PaymentProvider()),
      ],
      child: const FarmNexApp(),
    ),
  );
}

class FarmNexApp extends StatelessWidget {
  const FarmNexApp({super.key});

  @override
  Widget build(BuildContext context) {
    final langProvider = context.watch<LanguageProvider>();

    return MaterialApp(
      title: 'FarmNex',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      locale: Locale(langProvider.currentLanguage),
      supportedLocales: const [
        Locale('hi'),
        Locale('mr'),
        Locale('en'),
        Locale('te'),
        Locale('ta'),
        Locale('kn'),
        Locale('bn'),
        Locale('gu'),
      ],
      localizationsDelegates: const [
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
      home: const StartupScreen(),
    );
  }
}
