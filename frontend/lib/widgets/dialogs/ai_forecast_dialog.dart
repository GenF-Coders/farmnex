import '../auto_translated_text.dart';
import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../models/crop_model.dart';

class ForecastDayData {
  final String day;
  final double price;
  final String demand;
  final String volume;

  const ForecastDayData({
    required this.day,
    required this.price,
    required this.demand,
    required this.volume,
  });
}

class AIForecastDialog extends StatefulWidget {
  final CropItem crop;

  const AIForecastDialog({super.key, required this.crop});

  @override
  State<AIForecastDialog> createState() => _AIForecastDialogState();
}

class _AIForecastDialogState extends State<AIForecastDialog> {
  String _selectedMandi = 'A';

  final double mandiAPrice = 2450;
  final double mandiATransport = 4000;
  late double mandiANet;

  final double mandiBPrice = 2400;
  final double mandiBTransport = 2000;
  late double mandiBNet;

  late List<ForecastDayData> forecastDays;

  @override
  void initState() {
    super.initState();
    mandiANet = (mandiAPrice * 100) - mandiATransport;
    mandiBNet = (mandiBPrice * 100) - mandiBTransport;

    final base = widget.crop.currentPrice;
    forecastDays = [
      ForecastDayData(day: 'D1 (Today)', price: base, demand: 'High', volume: '1,200 Qtl'),
      ForecastDayData(day: 'D2', price: base + 20, demand: 'High', volume: '1,450 Qtl'),
      ForecastDayData(day: 'D3', price: base + 35, demand: 'Very High', volume: '1,900 Qtl'),
      ForecastDayData(day: 'D4', price: base + 50, demand: 'Very High', volume: '2,100 Qtl'),
      ForecastDayData(day: 'D5', price: base + 65, demand: 'Very High', volume: '2,300 Qtl'),
      ForecastDayData(day: 'D6', price: base + 80, demand: 'Peak', volume: '2,450 Qtl'),
      ForecastDayData(day: 'D7', price: base + 100, demand: 'Very High', volume: '2,200 Qtl'),
    ];
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      backgroundColor: Colors.white,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 540, maxHeight: 720),
        child: Column(
          children: [

            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [Color(0xFF166534), Color(0xFF0F766E)],
                ),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.auto_awesome, color: Color(0xFFFDE047), size: 22),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AutoTranslatedText(
                          'AI Demand Forecast & Net Realization',
                          style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w800),
                        ),
                        AutoTranslatedText(
                          '7-Day price prediction & APMC net profit engine',
                          style: TextStyle(color: Color(0xFFCCFBF1), fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [

                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF9FAFB),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.borderLight),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            AutoTranslatedText(widget.crop.emoji, style: const TextStyle(fontSize: 28)),
                            const SizedBox(width: 10),
                            Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                AutoTranslatedText(widget.crop.name, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
                                AutoTranslatedText(
                                  'Current Spot: ₹${widget.crop.currentPrice.toInt()} / ${widget.crop.unit}',
                                  style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                                ),
                              ],
                            ),
                          ],
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            AutoTranslatedText('7-Day Outlook', style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: const Color(0xFFDCFCE7),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: AutoTranslatedText(
                                '${widget.crop.aiDemand} Demand',
                                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Row(
                        children: [
                          Icon(Icons.bar_chart, color: AppTheme.primaryGreen, size: 18),
                          SizedBox(width: 6),
                          AutoTranslatedText('7-Day Price Trajectory', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.grey.shade100,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: AutoTranslatedText('XGBoost Model', style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  Container(
                    height: 150,
                    padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.borderLight),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: forecastDays.asMap().entries.map((entry) {
                        final idx = entry.key;
                        final item = entry.value;
                        final barHeight = 40.0 + (idx * 11.0);

                        return Column(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            AutoTranslatedText('₹${item.price.toInt()}', style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                            const SizedBox(height: 4),
                            Container(
                              width: 24,
                              height: barHeight,
                              decoration: BoxDecoration(
                                gradient: LinearGradient(
                                  begin: Alignment.bottomCenter,
                                  end: Alignment.topCenter,
                                  colors: [
                                    AppTheme.primaryGreen.withValues(alpha: 0.5),
                                    AppTheme.primaryGreen,
                                  ],
                                ),
                                borderRadius: BorderRadius.circular(6),
                              ),
                            ),
                            const SizedBox(height: 6),
                            AutoTranslatedText(item.day, style: const TextStyle(fontSize: 9, color: AppTheme.textMuted)),
                          ],
                        );
                      }).toList(),
                    ),
                  ),
                  const SizedBox(height: 20),

                  const Row(
                    children: [
                      Icon(Icons.calculate_outlined, color: AppTheme.accentAmber, size: 20),
                      SizedBox(width: 8),
                      AutoTranslatedText(
                        'Net Realization Calculator (परिवहन पश्चात शुद्ध मुनाफा)',
                        style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  AutoTranslatedText(
                    'Comparing 100 Quintals delivery between Central Mandi vs Local Mandi after subtracting diesel & transport costs:',
                    style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
                  ),
                  const SizedBox(height: 12),

                  Row(
                    children: [
                      Expanded(
                        child: InkWell(
                          onTap: () => setState(() => _selectedMandi = 'A'),
                          borderRadius: BorderRadius.circular(14),
                          child: Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: _selectedMandi == 'A' ? const Color(0xFFF0FDF4) : Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: _selectedMandi == 'A' ? AppTheme.primaryGreen : AppTheme.borderLight,
                                width: _selectedMandi == 'A' ? 2 : 1,
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    AutoTranslatedText('Mandi A (Indore)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                    if (_selectedMandi == 'A')
                                      const Icon(Icons.check_circle, color: AppTheme.primaryGreen, size: 16),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                AutoTranslatedText('Spot: ₹2,450/q', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                                AutoTranslatedText('Transport: -₹4,000', style: TextStyle(fontSize: 11, color: Colors.red)),
                                const Divider(height: 10),
                                AutoTranslatedText(
                                  'Net: ₹${mandiANet.toInt()}',
                                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: InkWell(
                          onTap: () => setState(() => _selectedMandi = 'B'),
                          borderRadius: BorderRadius.circular(14),
                          child: Container(
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: _selectedMandi == 'B' ? const Color(0xFFF0FDF4) : Colors.white,
                              borderRadius: BorderRadius.circular(14),
                              border: Border.all(
                                color: _selectedMandi == 'B' ? AppTheme.primaryGreen : AppTheme.borderLight,
                                width: _selectedMandi == 'B' ? 2 : 1,
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                  children: [
                                    AutoTranslatedText('Mandi B (Ujjain)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                                    if (_selectedMandi == 'B')
                                      const Icon(Icons.check_circle, color: AppTheme.primaryGreen, size: 16),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                AutoTranslatedText('Spot: ₹2,400/q', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                                AutoTranslatedText('Transport: -₹2,000', style: TextStyle(fontSize: 11, color: Colors.red)),
                                const Divider(height: 10),
                                AutoTranslatedText(
                                  'Net: ₹${mandiBNet.toInt()}',
                                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppTheme.textDark),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 14),

                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFFECFDF5),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFFA7F3D0)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.stars, color: AppTheme.primaryGreen, size: 24),
                        SizedBox(width: 10),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              AutoTranslatedText(
                                'AI Recommendation: Route to Mandi A (Indore Central)',
                                style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold, color: Color(0xFF065F46)),
                              ),
                              SizedBox(height: 2),
                              AutoTranslatedText(
                                'Despite ₹2,000 higher transport deduction, the ₹50/q rate premium yields +₹3,000 net extra profit for your 100 quintal lot.',
                                style: TextStyle(fontSize: 11, color: Color(0xFF047857), height: 1.3),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
