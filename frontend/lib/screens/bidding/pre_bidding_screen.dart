import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/bidding_provider.dart';
import '../../providers/market_provider.dart';
import '../../widgets/dialogs/crop_pre_bidding_dialog.dart';
import '../../widgets/crop_media_uploader.dart';

class PreBiddingScreen extends StatefulWidget {
  const PreBiddingScreen({super.key});

  @override
  State<PreBiddingScreen> createState() => _PreBiddingScreenState();
}

class _PreBiddingScreenState extends State<PreBiddingScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<BiddingProvider>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final market = context.watch<MarketProvider>();
    final bidding = context.watch<BiddingProvider>();
    final loggedIn = context.watch<AuthProvider>().isLoggedIn;
    final openEvents = bidding.events.where((e) => e.isOpen).length;
    final myBids = bidding.bids.length;
    final preBiddingCrops = market.crops.where((c) => c.biddingActive).toList();

    return RefreshIndicator(
      color: AppTheme.primaryGreen,
      onRefresh: () => Future.wait([context.read<MarketProvider>().load(), context.read<BiddingProvider>().load()]),
      child: ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
      children: [

        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF14532D), Color(0xFF1C1917)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: const Color(0xFF4ADE80),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: AutoTranslatedText(
                      'PRE-HARVEST',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Color(0xFF052E16)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  AutoTranslatedText(
                    'Sell before harvest',
                    style: TextStyle(fontSize: 11, color: Color(0xFFBBF7D0)),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              AutoTranslatedText(
                'Pre-harvest bidding',
                style: TextStyle(fontSize: 21, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              const SizedBox(height: 4),
              AutoTranslatedText(
                'Buyers bid on your crop up to 7 days before harvest. You pick the best offer.',
                style: TextStyle(fontSize: 14, color: Color(0xFFE5E7EB), height: 1.35),
              ),
              const SizedBox(height: 16),

              Row(
                children: [
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const AutoTranslatedText('Open for bidding', style: TextStyle(fontSize: 13, color: Color(0xFFBBF7D0))),
                          AutoTranslatedText('$openEvents', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Colors.white)),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const AutoTranslatedText('Bids', style: TextStyle(fontSize: 13, color: Color(0xFFBBF7D0))),
                          AutoTranslatedText('$myBids', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900, color: Color(0xFF86EFAC))),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFFF0FDF4),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFBBF7D0)),
          ),
          child: const Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.timer_outlined, color: AppTheme.primaryGreen, size: 20),
              SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      'How it works',
                      style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Color(0xFF166534)),
                    ),
                    SizedBox(height: 2),
                    AutoTranslatedText(
                      'Bidding opens 7 days before harvest. In the last 2 days, AI shows the best price you can expect.',
                      style: TextStyle(fontSize: 13, color: Color(0xFF15803D), height: 1.35),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),

        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            AutoTranslatedText('Open for bidding', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
            AutoTranslatedText('${preBiddingCrops.length} crops', style: const TextStyle(fontSize: 13, color: AppTheme.textMuted)),
          ],
        ),
        const SizedBox(height: 12),

        if (preBiddingCrops.isEmpty)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 28),
            decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(18), border: Border.all(color: AppTheme.borderLight)),
            child: Column(children: [
              const Icon(Icons.gavel_rounded, size: 40, color: AppTheme.primaryGreen),
              const SizedBox(height: 10),
              AutoTranslatedText(!loggedIn ? 'Log in to see crops open for bidding' : market.isLoading ? 'Loading…' : 'No crop is open for bidding yet',
                  textAlign: TextAlign.center, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
              const SizedBox(height: 6),
              const AutoTranslatedText('Farmers: list a crop and turn on “Pre-bid”. Pull down to refresh.',
                  textAlign: TextAlign.center, style: TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.35)),
            ]),
          ),

        ...preBiddingCrops.map((crop) => InkWell(
              onTap: () => showDialog(
                context: context,
                builder: (_) => CropPreBiddingDialog(crop: crop),
              ),
              borderRadius: BorderRadius.circular(20),
              child: Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppTheme.borderLight),
                ),
                child: Column(
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: const Color(0xFFF9FAFB),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: AutoTranslatedText(crop.emoji, style: const TextStyle(fontSize: 26)),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              AutoTranslatedText(crop.name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                              AutoTranslatedText('${crop.location} • Farmer: ${crop.farmerName}', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                            ],
                          ),
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            AutoTranslatedText('₹${crop.currentPrice.toInt()}', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
                            AutoTranslatedText('per ${crop.unit}', style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    CropMediaGallery(cropId: crop.id),
                    CropMediaUploader(cropId: crop.id, cropName: crop.name, farmerName: crop.farmerName),
                    const SizedBox(height: 8),

                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                      decoration: BoxDecoration(
                        color: const Color(0xFFF9FAFB),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Row(
                            children: [
                              const Icon(Icons.schedule, size: 14, color: AppTheme.primaryGreen),
                              const SizedBox(width: 4),
                              AutoTranslatedText(bidding.openEventForListing(crop.id) != null ? 'Bidding is open' : 'Bidding not opened yet', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
                            ],
                          ),
                          if (crop.lastTwoDaysAIActive && crop.expectedMaxPrice != null)
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFFFEF3C7),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: AutoTranslatedText(
                                'Max AI Target: ₹${crop.expectedMaxPrice!.toInt()}/q',
                                style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: Color(0xFF92400E)),
                              ),
                            )
                          else
                            AutoTranslatedText('${bidding.openEventForListing(crop.id)?.minimumIncrement.toStringAsFixed(0) ?? '-'} min step', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        AutoTranslatedText(
                          'See bids & AI price  →',
                          style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            )),
      ],
      ),
    );
  }
}
