import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/bid_model.dart';
import '../../models/crop_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/bidding_provider.dart';
import '../../providers/market_provider.dart';
import '../../widgets/symbol_widgets.dart';
import '../payment/checkout_screen.dart';

class BuyerBidsScreen extends StatelessWidget {
  const BuyerBidsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final bidding = context.watch<BiddingProvider>();
    final market = context.watch<MarketProvider>();
    final buyerName = auth.user?.name ?? '';

    final entries = <_MyBid>[];
    for (final crop in market.crops) {
      final myBids = bidding.getBidsForCrop(crop.id).where((b) => _isMine(b, buyerName)).toList();
      for (final bid in myBids) {
        final highest = bidding.getHighestBid(crop.id, crop.currentPrice);
        entries.add(_MyBid(crop: crop, bid: bid, highest: highest));
      }
    }

    final winning = entries.where((e) => e.bid.amount >= e.highest).length;
    final outbid = entries.length - winning;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(child: SymbolStat(symbol: '⚖️', value: '${entries.length}', caption: 'My bids')),
            const SizedBox(width: 10),
            Expanded(child: SymbolStat(symbol: '🥇', value: '$winning', caption: 'Highest')),
            const SizedBox(width: 10),
            Expanded(child: SymbolStat(symbol: '⚠️', value: '$outbid', caption: 'Outbid', color: AppTheme.alertRed)),
          ],
        ),
        const SizedBox(height: 20),
        const SectionHeader(symbol: '⚖️', title: 'My bidding activity'),
        if (entries.isEmpty)
          const Padding(
            padding: EdgeInsets.only(top: 30),
            child: SymbolEmptyState(symbol: '⚖️', message: 'Your bids will appear here after you place a bid.'),
          )
        else
          ...entries.map((entry) => _BidTile(entry: entry)),
      ],
    );
  }

  static bool _isMine(LiveBid bid, String buyerName) {
    if (buyerName.isEmpty) return bid.buyerName.endsWith('(You)');
    return bid.buyerName == '$buyerName (You)' || bid.buyerName == buyerName;
  }
}

class _MyBid {
  final CropItem crop;
  final LiveBid bid;
  final double highest;
  const _MyBid({required this.crop, required this.bid, required this.highest});
}

class _BidTile extends StatelessWidget {
  final _MyBid entry;
  const _BidTile({required this.entry});

  Future<void> _pay(BuildContext context) async {
    await Navigator.of(context).push<bool>(
      MaterialPageRoute(
        builder: (_) => CheckoutScreen(
          title: 'Settle winning bid',
          items: [
            CheckoutItem(
              cropId: entry.crop.id,
              name: entry.crop.name,
              emoji: entry.crop.emoji,
              quantity: entry.crop.quantityAvailable > 0 ? entry.crop.quantityAvailable : 1,
              unit: entry.crop.unit,
              pricePerUnit: entry.bid.amount,
              farmerName: entry.crop.farmerName,
              location: entry.crop.location,
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final isHighest = entry.bid.amount >= entry.highest;
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              AutoTranslatedText(entry.crop.emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(entry.crop.name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800)),
                    AutoTranslatedText('${entry.crop.farmerName} • ${entry.crop.location}', style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted)),
                  ],
                ),
              ),
              AutoTranslatedText(isHighest ? '🥇 Highest' : '⚠️ Outbid', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: isHighest ? AppTheme.primaryGreen : AppTheme.alertRed)),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: _price('Your bid', entry.bid.amount)),
              Expanded(child: _price('Current highest', entry.highest)),
            ],
          ),
          const SizedBox(height: 8),
          AutoTranslatedText(entry.bid.timestamp, style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
          if (isHighest) ...[
            const SizedBox(height: 10),
            SizedBox(width: double.infinity, child: ElevatedButton.icon(onPressed: () => _pay(context), icon: const Icon(Icons.lock_outline, size: 16), label: AutoTranslatedText('Continue to payment'))),
          ],
        ],
      ),
    );
  }

  Widget _price(String label, double value) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AutoTranslatedText(label, style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
          AutoTranslatedText(formatRupees(value), style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
        ],
      );
}
