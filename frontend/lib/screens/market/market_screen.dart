import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/guards/auth_guard.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/market_provider.dart';
import '../../models/user_model.dart';
import '../../widgets/apmc_ticker.dart';
import '../../widgets/crop_picture.dart';
import '../../widgets/crop_media_uploader.dart';
import '../../widgets/dialogs/ai_forecast_dialog.dart';
import '../../widgets/dialogs/crop_pre_bidding_dialog.dart';
import '../payment/checkout_screen.dart';

class MarketScreen extends StatelessWidget {
  const MarketScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final market = context.watch<MarketProvider>();
    final crops = market.filteredCrops;
    return RefreshIndicator(
      onRefresh: () async => Future<void>.delayed(const Duration(milliseconds: 500)),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 24),
        children: [
          _marketHeader(),
          const SizedBox(height: 10),
          _categoryBar(market),
          const SizedBox(height: 12),
          const ApmcTickerBar(),
          const SizedBox(height: 16),
          Row(children: [const Expanded(child: AutoTranslatedText('Fresh farmer listings', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900))), AutoTranslatedText('${crops.length} items', style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted))]),
          const SizedBox(height: 10),
          if (crops.isEmpty)
            _empty()
          else
            LayoutBuilder(builder: (context, constraints) {
              final columns = constraints.maxWidth >= 1100 ? 4 : constraints.maxWidth >= 700 ? 3 : 2;
              return GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: crops.length,
                gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: columns,
                  crossAxisSpacing: 10,
                  mainAxisSpacing: 10,
                  childAspectRatio: constraints.maxWidth >= 700 ? 0.69 : 0.57,
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
          AutoTranslatedText('Mandi & farmer marketplace', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
          SizedBox(height: 3),
          AutoTranslatedText('Browse produce, compare farmer lots, watch prices and inspect crop photos or videos.', style: TextStyle(fontSize: 10.8, color: AppTheme.textMuted, height: 1.35)),
        ]),
      );

  Widget _categoryBar(MarketProvider market) => SizedBox(
        height: 42,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: market.categories.length,
          separatorBuilder: (_, __) => const SizedBox(width: 7),
          itemBuilder: (_, i) {
            final cat = market.categories[i];
            final selected = market.selectedCategory == cat;
            return ChoiceChip(label: AutoTranslatedText(cat), selected: selected, onSelected: (_) => market.setCategory(cat), selectedColor: AppTheme.primaryGreen, labelStyle: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: selected ? Colors.white : AppTheme.textDark), side: BorderSide(color: selected ? AppTheme.primaryGreen : AppTheme.borderLight));
          },
        ),
      );

  Widget _empty() => Container(padding: const EdgeInsets.all(28), decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(14), border: Border.all(color: AppTheme.borderLight)), child: const Column(children: [Icon(Icons.search_off_rounded, color: AppTheme.textMuted, size: 32), SizedBox(height: 8), AutoTranslatedText('No produce found', style: TextStyle(fontWeight: FontWeight.w800)), SizedBox(height: 3), AutoTranslatedText('Try another search or category.', style: TextStyle(fontSize: 11, color: AppTheme.textMuted))]));
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

  @override
  Widget build(BuildContext context) {
    return Card(
      clipBehavior: Clip.antiAlias,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14), side: const BorderSide(color: AppTheme.borderLight)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        AspectRatio(aspectRatio: 1.55, child: Stack(fit: StackFit.expand, children: [Container(color: const Color(0xFFF6F8F3), padding: const EdgeInsets.all(8), child: CropPicture(cropName: crop.name, fallbackEmoji: crop.emoji, size: 200, borderRadius: BorderRadius.circular(10))), Positioned(left: 8, top: 8, child: Container(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 4), decoration: BoxDecoration(color: Colors.white.withValues(alpha: .94), borderRadius: BorderRadius.circular(7)), child: AutoTranslatedText(crop.category, style: const TextStyle(fontSize: 8.5, fontWeight: FontWeight.w800, color: AppTheme.primaryGreen))))])),
        Padding(padding: const EdgeInsets.fromLTRB(9, 9, 9, 9), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          AutoTranslatedText(crop.name, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w900)),
          const SizedBox(height: 3),
          AutoTranslatedText(crop.variety, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 9.5, color: AppTheme.textMuted)),
          const SizedBox(height: 6),
          AutoTranslatedText('₹${crop.currentPrice.toInt()} / ${crop.unit}', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
          const SizedBox(height: 3),
          AutoTranslatedText('${crop.location} • ${crop.quantityAvailable} ${crop.unit}s', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 9, color: AppTheme.textMuted)),
          const SizedBox(height: 8),
          Row(children: [Expanded(child: OutlinedButton(onPressed: () => showDialog(context: context, builder: (_) => CropPreBiddingDialog(crop: crop)), style: OutlinedButton.styleFrom(minimumSize: const Size(0, 34), padding: const EdgeInsets.symmetric(horizontal: 5), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), child: AutoTranslatedText(crop.biddingActive ? 'Pre-bid' : 'Inspect', style: const TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800)))), const SizedBox(width: 6), Expanded(child: ElevatedButton(onPressed: () => _buy(context), style: ElevatedButton.styleFrom(minimumSize: const Size(0, 34), padding: const EdgeInsets.symmetric(horizontal: 5), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8))), child: AutoTranslatedText('Buy', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w900))))]),
          const SizedBox(height: 6),
          Row(children: [Expanded(child: TextButton(onPressed: () => showDialog(context: context, builder: (_) => AIForecastDialog(crop: crop)), child: AutoTranslatedText('Price insight', style: TextStyle(fontSize: 9.5, color: AppTheme.primaryGreen, fontWeight: FontWeight.w800)))), const Icon(Icons.location_on_outlined, size: 13, color: AppTheme.textMuted)]),
          const SizedBox(height: 4),
          ClipRRect(borderRadius: BorderRadius.circular(8), child: Container(height: 64, color: const Color(0xFFF8FAF7), child: CropMediaGallery(cropId: crop.id))),
          Consumer<AuthProvider>(builder: (context, auth, _) => auth.isLoggedIn && auth.user?.role == UserRole.farmer ? Padding(padding: const EdgeInsets.only(top: 6), child: CropMediaUploader(cropId: crop.id, cropName: crop.name, farmerName: crop.farmerName)) : const SizedBox.shrink()),
        ])),
      ]),
    );
  }
}
