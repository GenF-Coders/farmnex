import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/guards/auth_guard.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/market_provider.dart';
import '../../widgets/apmc_ticker.dart';
import '../../widgets/crop_picture.dart';
import '../../widgets/dialogs/ai_forecast_dialog.dart';
import '../../widgets/dialogs/crop_pre_bidding_dialog.dart';
import '../payment/checkout_screen.dart';

class MarketScreen extends StatefulWidget {
  const MarketScreen({super.key});

  @override
  State<MarketScreen> createState() => _MarketScreenState();
}

class _MarketScreenState extends State<MarketScreen> {
  bool? _loadedForLogin;

  @override
  Widget build(BuildContext context) {
    final market = context.watch<MarketProvider>();
    final loggedIn = context.watch<AuthProvider>().isLoggedIn;
    if (_loadedForLogin != loggedIn) {
      // First open, or someone logged in / out: fetch the lots again.
      _loadedForLogin = loggedIn;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        context.read<MarketProvider>().load();
      });
    }
    final crops = market.filteredCrops;
    return RefreshIndicator(
      onRefresh: () => context.read<MarketProvider>().load(),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 24),
        children: [
          _marketHeader(),
          const SizedBox(height: 10),
          _categoryBar(market),
          const SizedBox(height: 12),
          const ApmcTickerBar(),
          const SizedBox(height: 16),
          Row(children: [const Expanded(child: AutoTranslatedText('Fresh farmer listings', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900))), AutoTranslatedText('${crops.length} items', style: const TextStyle(fontSize: 13, color: AppTheme.textMuted))]),
          const SizedBox(height: 10),
          if (market.isLoading && crops.isEmpty)
            const Padding(padding: EdgeInsets.all(28), child: Center(child: CircularProgressIndicator()))
          else if (market.error != null && crops.isEmpty)
            _error(market.error!, () => context.read<MarketProvider>().load())
          else if (crops.isEmpty)
            _empty()
          else
            LayoutBuilder(builder: (context, constraints) {
              final columns = constraints.maxWidth >= 1100 ? 4 : constraints.maxWidth >= 700 ? 3 : 2;
              return GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: crops.length,
                // Height = picture + text block; the text block grows with the phone's text size.
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: columns,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                  mainAxisExtent: (constraints.maxWidth - 12 * (columns - 1)) / columns / 1.55 +
                      MediaQuery.textScalerOf(context).scale(100) * 1.55 + 70,
                ),
                itemBuilder: (_, i) => _MarketProductCard(crop: crops[i]),
              );
            }),
        ],
      ),
    );
  }

  Widget _marketHeader() => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppTheme.borderLight)),
        child: const Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          AutoTranslatedText('Mandi & farmer marketplace', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
          SizedBox(height: 3),
          AutoTranslatedText('Buy fresh produce directly from farmers.', style: TextStyle(fontSize: 14, color: AppTheme.textMuted, height: 1.35)),
        ]),
      );

  Widget _categoryBar(MarketProvider market) => SizedBox(
        height: 48,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: market.categories.length,
          separatorBuilder: (_, __) => const SizedBox(width: 7),
          itemBuilder: (_, i) {
            final cat = market.categories[i];
            final selected = market.selectedCategory == cat;
            return ChoiceChip(label: AutoTranslatedText(cat), selected: selected, onSelected: (_) => market.setCategory(cat), selectedColor: AppTheme.primaryGreen, labelStyle: TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: selected ? Colors.white : AppTheme.textDark), side: BorderSide(color: selected ? AppTheme.primaryGreen : AppTheme.borderLight));
          },
        ),
      );

  Widget _error(String message, VoidCallback onRetry) => Container(
        padding: const EdgeInsets.all(28),
        decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppTheme.borderLight)),
        child: Column(children: [
          const Icon(Icons.cloud_off_rounded, color: AppTheme.textMuted, size: 32),
          const SizedBox(height: 8),
          AutoTranslatedText(message, textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w800)),
          const SizedBox(height: 10),
          OutlinedButton(onPressed: onRetry, child: const AutoTranslatedText('Try again')),
        ]),
      );

  Widget _empty() => Container(padding: const EdgeInsets.all(28), decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppTheme.borderLight)), child: const Column(children: [Icon(Icons.search_off_rounded, color: AppTheme.textMuted, size: 32), SizedBox(height: 8), AutoTranslatedText('No produce found', style: TextStyle(fontWeight: FontWeight.w800)), SizedBox(height: 3), AutoTranslatedText('Try another search or category.', style: TextStyle(fontSize: 13, color: AppTheme.textMuted))]));
}

class _MarketProductCard extends StatelessWidget {
  final dynamic crop;
  const _MarketProductCard({required this.crop});

  void _buy(BuildContext context) {
    final auth = context.read<AuthProvider>();
    AuthGuard.requireAuth(
      context: context,
      authProvider: auth,
      actionType: 'buy',
      cropId: crop.id,
      cropName: crop.name,
      onAuthenticated: () {
        final quantity = crop.quantityAvailable >= 10 ? 10 : crop.quantityAvailable;
        Navigator.of(context).push<bool>(MaterialPageRoute(builder: (_) => CheckoutScreen(title: 'Buy direct', items: [CheckoutItem(cropId: crop.id, name: crop.name, emoji: crop.emoji, quantity: quantity <= 0 ? 1 : quantity, unit: crop.unit, pricePerUnit: crop.currentPrice, farmerName: crop.farmerName, location: crop.location)])));
      },
    );
  }

  void _inspect(BuildContext context) => showDialog<void>(context: context, builder: (_) => CropPreBiddingDialog(crop: crop));

  @override
  Widget build(BuildContext context) {
    // One main action per card: "Buy" for a fixed-price lot, "Place bid" for a pre-bid lot
    // (the server refuses a direct buy on a pre-bid lot). Tapping the card shows its details.
    final bool preBid = crop.biddingActive;
    return Card(
      clipBehavior: Clip.antiAlias,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppTheme.borderLight)),
      child: InkWell(
        onTap: () => _inspect(context),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          AspectRatio(aspectRatio: 1.55, child: Stack(fit: StackFit.expand, children: [
            Container(color: const Color(0xFFF6F8F3), padding: const EdgeInsets.all(8), child: CropPicture(cropName: crop.name, fallbackEmoji: crop.emoji, size: 200, borderRadius: BorderRadius.circular(10))),
            Positioned(left: 8, top: 8, child: _Tag(text: preBid ? 'Pre-bid' : crop.category, color: preBid ? AppTheme.accentAmber : AppTheme.primaryGreen)),
            if (crop.verificationStatus == 'VERIFIED')
              const Positioned(right: 8, top: 8, child: _Tag(text: '✅ Verified', color: AppTheme.primaryGreen)),
          ])),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(10, 10, 10, 8),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                AutoTranslatedText(crop.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
                const SizedBox(height: 3),
                AutoTranslatedText('₹${crop.currentPrice.toInt()} / ${crop.unit}', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
                const SizedBox(height: 3),
                AutoTranslatedText('${crop.location.isEmpty ? '' : '${crop.location} • '}${crop.quantityAvailable} ${crop.unit}', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                const Spacer(),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () => preBid ? _inspect(context) : _buy(context),
                    style: ElevatedButton.styleFrom(
                      minimumSize: const Size(0, 42),
                      padding: const EdgeInsets.symmetric(horizontal: 6),
                      backgroundColor: preBid ? AppTheme.accentAmber : AppTheme.primaryGreen,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: AutoTranslatedText(preBid ? 'Place bid' : 'Buy', maxLines: 1, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900)),
                  ),
                ),
                SizedBox(
                  width: double.infinity,
                  child: TextButton.icon(
                    onPressed: () => showDialog<void>(context: context, builder: (_) => AIForecastDialog(crop: crop)),
                    style: TextButton.styleFrom(minimumSize: const Size(0, 36), padding: EdgeInsets.zero),
                    icon: const Icon(Icons.insights_rounded, size: 16),
                    label: const AutoTranslatedText('Price forecast', maxLines: 1, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                  ),
                ),
              ]),
            ),
          ),
        ]),
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  final String text;
  final Color color;
  const _Tag({required this.text, required this.color});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
        decoration: BoxDecoration(color: Colors.white.withValues(alpha: .95), borderRadius: BorderRadius.circular(20)),
        child: AutoTranslatedText(text, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: color)),
      );
}
