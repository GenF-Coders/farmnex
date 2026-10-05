import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../localization/l10n_extension.dart';
import '../../models/rescue_listing_model.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/rescue_provider.dart';
import '../../widgets/auto_translated_text.dart';
import '../../widgets/symbol_widgets.dart';
import 'buyer_rescue_view.dart';
import 'publish_rescue_sheet.dart';
import 'rescue_detail_screen.dart';

/// Crop Rescue is for farmers only (the backend answers 403 to everyone else).
class CropRescueScreen extends StatelessWidget {
  const CropRescueScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isFarmer = auth.isLoggedIn && auth.user?.role == UserRole.farmer;
    return isFarmer ? const _FarmerRescueView() : const BuyerRescueView();
  }
}

String rescueStatusLabel(String status) => switch (status) {
      'AT_RISK' => 'At risk',
      'SPOILED' => 'Spoiled',
      'SOLD' => 'Sold',
      _ => 'Fresh',
    };

String rescueStatusSymbol(String status) => switch (status) {
      'AT_RISK' => '🟠',
      'SPOILED' => '🔴',
      'SOLD' => '✅',
      _ => '🟢',
    };

Color rescueStatusColor(String status) => switch (status) {
      'AT_RISK' => AppTheme.accentAmber,
      'SPOILED' => AppTheme.alertRed,
      'SOLD' => AppTheme.accentTeal,
      _ => AppTheme.primaryGreen,
    };

/// "2 days 4 h left", "5 h left", or "Spoiled" ("… (estimate)" for crops without researched data).
String rescueTimeLeft(RescueLot lot) {
  if (lot.status == 'SOLD') return 'Sold';
  final hours = lot.remainingHours;
  if (lot.status == 'SPOILED' || hours == null || hours <= 0) return 'Spoiled';
  final note = lot.estimate ? ' (estimate)' : '';
  if (hours >= 48) return '${(hours / 24).floor()} days ${(hours % 24).round()} h left$note';
  return '${hours.round()} h left$note';
}

class _FarmerRescueView extends StatefulWidget {
  const _FarmerRescueView();

  @override
  State<_FarmerRescueView> createState() => _FarmerRescueViewState();
}

class _FarmerRescueViewState extends State<_FarmerRescueView> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<RescueProvider>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final rescue = context.watch<RescueProvider>();
    final lots = rescue.lots;

    Widget body;
    if (!rescue.loaded && rescue.isLoading) {
      body = const Center(child: CircularProgressIndicator());
    } else if (!rescue.loaded && rescue.errorMessage != null) {
      body = SymbolEmptyState(
        symbol: '⚠️',
        message: rescue.errorMessage!,
        actionLabel: context.t('retry'),
        onAction: rescue.load,
      );
    } else {
      body = RefreshIndicator(
        color: AppTheme.primaryGreen,
        onRefresh: rescue.load,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
          children: [
            Row(children: [
              Expanded(child: SymbolStat(symbol: '🟢', value: '${rescue.openCount}', caption: 'Being watched')),
              const SizedBox(width: 10),
              Expanded(
                child: SymbolStat(
                  symbol: '🟠',
                  value: '${rescue.atRiskCount}',
                  caption: 'At risk',
                  color: AppTheme.accentAmber,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: SymbolStat(
                  symbol: '✅',
                  value: '${rescue.soldCount}',
                  caption: 'Sold',
                  color: AppTheme.accentTeal,
                ),
              ),
            ]),
            if (rescue.errorMessage != null) ...[
              const SizedBox(height: 12),
              _ErrorStrip(message: rescue.errorMessage!),
            ],
            const SizedBox(height: 20),
            SectionHeader(symbol: '🚨', title: context.t('my_rescue_lots')),
            if (lots.isEmpty)
              SymbolEmptyState(
                symbol: '🌾',
                message: 'No lots yet. Register a harvested lot and we will warn you before it spoils.',
                actionLabel: 'Register a lot',
                onAction: () => openPublishRescueSheet(context),
              )
            else
              ...lots.map((l) => _LotCard(lot: l)),
          ],
        ),
      );
    }

    // When the list is empty its own "Register a lot" button is shown, so no second (floating) one.
    if (lots.isEmpty) return body;
    return Stack(children: [
      body,
      Positioned(
        right: 16,
        bottom: 16,
        child: FloatingActionButton.extended(
          onPressed: () => openPublishRescueSheet(context),
          backgroundColor: AppTheme.primaryGreen,
          foregroundColor: Colors.white,
          icon: const Icon(Icons.add),
          label: const AutoTranslatedText('Register a lot', style: TextStyle(fontWeight: FontWeight.w800)),
        ),
      ),
    ]);
  }
}

class _ErrorStrip extends StatelessWidget {
  final String message;
  const _ErrorStrip({required this.message});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppTheme.alertRed.withValues(alpha: .08),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(children: [
          const Icon(Icons.error_outline, size: 18, color: AppTheme.alertRed),
          const SizedBox(width: 8),
          Expanded(child: AutoTranslatedText(message, style: const TextStyle(fontSize: 13))),
          IconButton(
            icon: const Icon(Icons.close, size: 16),
            onPressed: context.read<RescueProvider>().clearError,
          ),
        ]),
      );
}

class _LotCard extends StatelessWidget {
  final RescueLot lot;
  const _LotCard({required this.lot});

  @override
  Widget build(BuildContext context) {
    final rescue = context.read<RescueProvider>();
    final color = rescueStatusColor(lot.status);
    return InkWell(
      onTap: () => Navigator.of(context).push<void>(
        MaterialPageRoute(builder: (_) => RescueDetailScreen(lotId: lot.id)),
      ),
      borderRadius: BorderRadius.circular(18),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: lot.isAtRisk ? color : AppTheme.borderLight),
        ),
        child: Row(children: [
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              AutoTranslatedText(
                rescue.cropName(lot.cropCode),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              AutoTranslatedText(
                '📦 ${lot.quantityKg.round()} kg   ⏳ ${rescueTimeLeft(lot)}',
                style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
              ),
            ]),
          ),
          StatusPill(
            symbol: rescueStatusSymbol(lot.status),
            label: rescueStatusLabel(lot.status),
            color: color,
          ),
          const Icon(Icons.chevron_right_rounded, color: AppTheme.textMuted),
        ]),
      ),
    );
  }
}
