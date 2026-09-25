import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:farmnex_flutter/main.dart';
import 'package:farmnex_flutter/localization/language_provider.dart';
import 'package:farmnex_flutter/providers/auth_provider.dart';
import 'package:farmnex_flutter/providers/bidding_provider.dart';
import 'package:farmnex_flutter/providers/market_provider.dart';
import 'package:farmnex_flutter/providers/rescue_provider.dart';
import 'package:farmnex_flutter/providers/verification_provider.dart';
import 'package:farmnex_flutter/providers/waste_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  testWidgets('FarmNexApp smoke test - renders title and bottom navigation',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider(create: (_) => LanguageProvider()),
          ChangeNotifierProvider(create: (_) => AuthProvider()),
          ChangeNotifierProvider(create: (_) => MarketProvider()),
          ChangeNotifierProvider(create: (_) => BiddingProvider()),
          ChangeNotifierProvider(create: (_) => RescueProvider()),
          ChangeNotifierProvider(create: (_) => WasteProvider()),
          ChangeNotifierProvider(create: (_) => VerificationProvider()),
        ],
        child: const FarmNexApp(),
      ),
    );

    await tester.pumpAndSettle();

    expect(find.text('STARK / FARMNEX'), findsOneWidget);

    expect(find.text('AI Voice Assistant'), findsOneWidget);
  });

  test('MarketProvider unit test - default crops and categories', () {
    final provider = MarketProvider();
    expect(provider.crops.isNotEmpty, true);
    expect(provider.categories.contains('All'), true);
    expect(provider.filteredCrops.length, provider.crops.length);

    provider.setCategory('Grains');
    expect(provider.filteredCrops.every((c) => c.category == 'Grains'), true);
  });

  test('BiddingProvider unit test - placing bid sets highest bid', () {
    final bidding = BiddingProvider();
    final initialHighest = bidding.getHighestBid('crop-1', 2450);

    bidding.placeBid(
      cropId: 'crop-1',
      buyerName: 'Test Buyer',
      companyName: 'Test Firm',
      amount: initialHighest + 100,
    );

    final newHighest = bidding.getHighestBid('crop-1', 2450);
    expect(newHighest, initialHighest + 100);
  });
}
