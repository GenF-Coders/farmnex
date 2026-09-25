import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/market_provider.dart';
import '../../widgets/dialogs/crop_pre_bidding_dialog.dart';
import '../../widgets/crop_media_uploader.dart';

class PreBiddingScreen extends StatelessWidget {
  const PreBiddingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final market = context.watch<MarketProvider>();
    final preBiddingCrops = market.crops.where((c) => c.biddingActive).toList();

    return ListView(
      padding: const EdgeInsets.all(16),
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
                      'CONTRACT BIDDING',
                      style: TextStyle(fontSize: 10, fontWeight: FontWeight.w900, color: Color(0xFF052E16)),
                    ),
                  ),
                  const SizedBox(width: 8),
                  AutoTranslatedText(
                    '7-Day Pre-Harvest Protocol',
                    style: TextStyle(fontSize: 11, color: Color(0xFFBBF7D0)),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              AutoTranslatedText(
                'Crop Pre-Harvest Bidding Hub',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              const SizedBox(height: 4),
              AutoTranslatedText(
                'Live discovery where verified buyers lock in purchase commitments 7 days prior to harvest, with 48-hour AI Maximum Expected Price forecasting.',
                style: TextStyle(fontSize: 11.5, color: Color(0xFFE5E7EB), height: 1.3),
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
                      child: const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          AutoTranslatedText('Active Bids', style: TextStyle(fontSize: 11, color: Color(0xFFBBF7D0))),
                          AutoTranslatedText('24 Lots', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Colors.white)),
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
                      child: const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          AutoTranslatedText('Avg Premium', style: TextStyle(fontSize: 11, color: Color(0xFFBBF7D0))),
                          AutoTranslatedText('+12.4%', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900, color: Color(0xFF86EFAC))),
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
                      '7-Day Pre-Harvest Rule & 48-Hour AI Predictor',
                      style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: Color(0xFF166534)),
                    ),
                    SizedBox(height: 2),
                    AutoTranslatedText(
                      'Bids open strictly 7 days prior to harvest. In the final 48 hours, machine learning triggers real-time price predictions with confidence indicators.',
                      style: TextStyle(fontSize: 11, color: Color(0xFF15803D), height: 1.3),
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
            AutoTranslatedText('Lots in Active Pre-Harvest Window', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
            AutoTranslatedText('${preBiddingCrops.length} Active Lots', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
          ],
        ),
        const SizedBox(height: 12),

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
                              AutoTranslatedText('Harvest: ${crop.expectedHarvestDate}', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold)),
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
                            AutoTranslatedText('Bids open', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                        ],
                      ),
                    ),
                    const SizedBox(height: 12),

                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        AutoTranslatedText(
                          'Open Bid Room & AI Price →',
                          style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            )),
      ],
    );
  }
}
