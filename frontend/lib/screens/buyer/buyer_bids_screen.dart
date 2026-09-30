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

/// The signed-in buyer's own bids, from `GET /api/v2/bids`.
class BuyerBidsScreen extends StatefulWidget {
  const BuyerBidsScreen({super.key});

  @override
  State<BuyerBidsScreen> createState() => _BuyerBidsScreenState();
}

class _BuyerBidsScreenState extends State<BuyerBidsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<BiddingProvider>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final myId = context.watch<AuthProvider>().user?.id;
    final bidding = context.watch<BiddingProvider>();
    final market = context.watch<MarketProvider>();

    final mine = bidding.bids.where((b) => b.bidderId == myId).toList()
      ..sort((a, b) => b.placedAt.compareTo(a.placedAt));
    final entries = <_MyBid>[];
    for (final bid in mine) {
      final event = bidding.eventById(bid.bidEventId);
      CropItem? crop;
      if (event != null) {
        for (final c in market.crops) {
          if (c.id == event.listingId) crop = c;
        }
      }
      entries.add(_MyBid(bid: bid, event: event, crop: crop));
    }

    final won = entries.where((e) => e.bid.isWon).length;
    final waiting = entries.where((e) => e.bid.isActive).length;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(child: SymbolStat(symbol: '⚖️', value: '${entries.length}', caption: 'My bids')),
            const SizedBox(width: 10),
            Expanded(child: SymbolStat(symbol: '🥇', value: '$won', caption: 'Won')),
            const SizedBox(width: 10),
            Expanded(child: SymbolStat(symbol: '⏳', value: '$waiting', caption: 'Waiting')),
          ],
        ),
        const SizedBox(height: 20),
        const SectionHeader(symbol: '⚖️', title: 'My bidding activity'),
        if (bidding.error != null)
          Padding(
            padding: const EdgeInsets.only(top: 12),
            child: AutoTranslatedText(bidding.error!, style: const TextStyle(fontSize: 12, color: AppTheme.alertRed)),
          ),
        if (bidding.isLoading && entries.isEmpty)
          const Padding(padding: EdgeInsets.only(top: 30), child: Center(child: CircularProgressIndicator()))
        else if (entries.isEmpty)
          const Padding(
            padding: EdgeInsets.only(top: 30),
            child: SymbolEmptyState(symbol: '⚖️', message: 'Your bids will appear here after you place a bid.'),
          )
        else
          ...entries.map((entry) => _BidTile(entry: entry)),
      ],
    );
  }
}

class _MyBid {
  final BidModel bid;
  final BidEventModel? event;
  final CropItem? crop;
  const _MyBid({required this.bid, this.event, this.crop});
}

class _BidTile extends StatelessWidget {
  final _MyBid entry;
  const _BidTile({required this.entry});

  @override
  Widget build(BuildContext context) {
    final bid = entry.bid;
    final crop = entry.crop;
    final (label, color) = bid.isWon
        ? ('🥇 Won', AppTheme.primaryGreen)
        : bid.isLost
            ? ('Not accepted', AppTheme.textMuted)
            : ('⏳ Waiting for the farmer', const Color(0xFFD97706));
    final qty = bid.quantity == null ? '' : ' • ${bid.quantity!.toStringAsFixed(bid.quantity! % 1 == 0 ? 0 : 2)} ${crop?.unit ?? ''}';
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
              AutoTranslatedText(crop?.emoji ?? '🌱', style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(crop?.name ?? 'Pre-bid lot', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800)),
                    AutoTranslatedText('${bidTimeAgo(bid.placedAt)}$qty', style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted)),
                  ],
                ),
              ),
              AutoTranslatedText(label, style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: color)),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(child: _price('Your bid', bid.amount)),
              if (entry.event != null) Expanded(child: _price('Starting price', entry.event!.startingPrice)),
            ],
          ),
          if (bid.isWon) ...[
            const SizedBox(height: 10),
            const AutoTranslatedText(
              'The farmer accepted your bid. Your order is ready: pay it from My Orders.',
              style: TextStyle(fontSize: 11.5, color: AppTheme.primaryGreen, fontWeight: FontWeight.w700),
            ),
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
