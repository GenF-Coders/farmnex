import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/network/crop_rescue_api.dart';
import '../../core/theme/app_theme.dart';
import '../../models/rescue_listing_model.dart';
import '../../providers/rescue_provider.dart';
import '../../widgets/auto_translated_text.dart';
import '../../widgets/symbol_widgets.dart';
import 'crop_rescue_screen.dart';

/// One lot: how long it has left, the nearby buyers when it is at risk, and "mark sold".
class RescueDetailScreen extends StatefulWidget {
  final String lotId;

  const RescueDetailScreen({super.key, required this.lotId});

  @override
  State<RescueDetailScreen> createState() => _RescueDetailScreenState();
}

class _RescueDetailScreenState extends State<RescueDetailScreen> {
  List<RescueMatch>? _matches;
  String? _matchesError;
  String? _matchesFor;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<RescueProvider>().loadDetail(widget.lotId);
    });
  }

  Future<void> _loadMatches(RescueProvider rescue) async {
    // Re-fetch only when the status changed; the build method calls this.
    _matchesFor = 'AT_RISK';
    try {
      final list = await rescue.matchesFor(widget.lotId);
      if (mounted) setState(() { _matches = list; _matchesError = null; });
    } catch (e) {
      if (mounted) setState(() { _matches = null; _matchesError = rescueErrorMessage(e); });
    }
  }

  Future<void> _markSold(RescueProvider rescue) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: const AutoTranslatedText('Mark as sold?'),
        content: const AutoTranslatedText('We will stop watching this lot and stop sending alerts.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const AutoTranslatedText('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const AutoTranslatedText('Mark sold'),
          ),
        ],
      ),
    );
    if (ok == true) await rescue.markSold(widget.lotId);
  }

  @override
  Widget build(BuildContext context) {
    final rescue = context.watch<RescueProvider>();
    final lot = rescue.byId(widget.lotId);

    if (lot == null) {
      return Scaffold(
        appBar: AppBar(),
        body: SymbolEmptyState(symbol: '🔍', message: rescue.errorMessage ?? 'This lot was not found.'),
      );
    }

    if (lot.isAtRisk && _matchesFor != 'AT_RISK') {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) _loadMatches(rescue);
      });
    } else if (!lot.isAtRisk && _matchesFor != null) {
      _matchesFor = null;
      _matches = null;
    }

    final color = rescueStatusColor(lot.status);
    final harvested = lot.harvestedAt;

    return Scaffold(
      appBar: AppBar(title: AutoTranslatedText(rescue.cropName(lot.cropCode))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: color.withValues(alpha: .08),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: color),
            ),
            child: Column(children: [
              AutoTranslatedText(
                rescueTimeLeft(lot),
                style: TextStyle(fontSize: 26, fontWeight: FontWeight.w900, color: color),
              ),
              const SizedBox(height: 6),
              StatusPill(
                symbol: rescueStatusSymbol(lot.status),
                label: rescueStatusLabel(lot.status),
                color: color,
              ),
            ]),
          ),
          const SizedBox(height: 16),
          SymbolRow(symbol: '📦', label: 'Quantity', value: '${lot.quantityKg.round()} kg'),
          if (harvested != null)
            SymbolRow(symbol: '🌾', label: 'Harvested', value: '${harvested.day}/${harvested.month}/${harvested.year}'),
          SymbolRow(symbol: '🏠', label: 'Storage', value: lot.storageMode == 'cold' ? 'Cold storage' : 'Normal'),
          if (lot.floorPricePerKg > 0)
            SymbolRow(symbol: '💰', label: 'Lowest price you accept', value: '₹${lot.floorPricePerKg.round()}/kg'),
          if (rescue.errorMessage != null) ...[
            const SizedBox(height: 10),
            AutoTranslatedText(rescue.errorMessage!, style: const TextStyle(fontSize: 12, color: AppTheme.alertRed)),
          ],
          if (lot.isAtRisk) ...[
            const SizedBox(height: 20),
            const SectionHeader(symbol: '🛒', title: 'Nearby buyers'),
            if (_matchesError != null)
              AutoTranslatedText(_matchesError!, style: const TextStyle(fontSize: 12, color: AppTheme.alertRed))
            else if (_matches == null)
              const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator()))
            else if (_matches!.isEmpty)
              const AutoTranslatedText(
                'No buyers within range right now.',
                style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
              )
            else
              ..._matches!.map((m) => _MatchCard(match: m)),
          ],
          if (lot.isOpen) ...[
            const SizedBox(height: 20),
            SizedBox(
              height: 48,
              child: ElevatedButton.icon(
                onPressed: rescue.isSaving ? null : () => _markSold(rescue),
                icon: const Icon(Icons.check_circle_outline),
                label: const AutoTranslatedText('Mark as sold', style: TextStyle(fontWeight: FontWeight.w800)),
              ),
            ),
            const SizedBox(height: 10),
            // Demo helper. The server turns it off (404) after the demo, then the message shows.
            SizedBox(
              height: 44,
              child: OutlinedButton.icon(
                onPressed: rescue.isSaving ? null : () => rescue.fastForward(lot.id, 24),
                icon: const Icon(Icons.fast_forward),
                label: const AutoTranslatedText('Demo: skip ahead 24 hours'),
              ),
            ),
          ],
          if (lot.checks.isNotEmpty) ...[
            const SizedBox(height: 20),
            const SectionHeader(symbol: '🕒', title: 'Freshness checks'),
            ...lot.checks.take(10).map(
                  (c) => SymbolRow(
                    symbol: rescueStatusSymbol(c.status),
                    label: c.checkedAt == null
                        ? ''
                        : '${c.checkedAt!.day}/${c.checkedAt!.month} ${c.checkedAt!.hour.toString().padLeft(2, '0')}:${c.checkedAt!.minute.toString().padLeft(2, '0')}',
                    value: '${c.remainingHours.round()} h left · ${c.temperatureC.round()}°C',
                  ),
                ),
          ],
        ],
      ),
    );
  }
}

class _MatchCard extends StatelessWidget {
  final RescueMatch match;
  const _MatchCard({required this.match});

  @override
  Widget build(BuildContext context) => Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.borderLight),
        ),
        child: Row(children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              AutoTranslatedText(match.buyerName, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800)),
              const SizedBox(height: 2),
              AutoTranslatedText(
                '${match.distanceKm.round()} km · about ${match.travelHours.toStringAsFixed(1)} h away · wants ${match.qtyKg.round()} kg',
                style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
              ),
              if (match.reason.isNotEmpty)
                AutoTranslatedText(match.reason, style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
            ]),
          ),
          Column(crossAxisAlignment: CrossAxisAlignment.end, children: [
            AutoTranslatedText(
              '₹${match.netPricePerKg.toStringAsFixed(1)}',
              style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
            ),
            const AutoTranslatedText('/kg after transport', style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
          ]),
        ]),
      );
}
