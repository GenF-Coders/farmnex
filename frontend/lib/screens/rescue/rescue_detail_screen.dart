import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/guards/auth_guard.dart';
import '../../core/theme/app_theme.dart';
import '../../localization/l10n_extension.dart';
import '../../providers/auth_provider.dart';
import '../../providers/rescue_provider.dart';
import '../../widgets/symbol_widgets.dart';
import '../payment/checkout_screen.dart';

class RescueDetailScreen extends StatefulWidget {
  final String listingId;

  const RescueDetailScreen({super.key, required this.listingId});

  @override
  State<RescueDetailScreen> createState() => _RescueDetailScreenState();
}

class _RescueDetailScreenState extends State<RescueDetailScreen> {
  int _quantity = 0;

  @override
  Widget build(BuildContext context) {
    final rescue = context.watch<RescueProvider>();
    final listing = rescue.byId(widget.listingId);

    if (listing == null) {
      return Scaffold(
        appBar: AppBar(),
        body: SymbolEmptyState(symbol: '🔍', message: context.t('listing_unavailable')),
      );
    }

    final maxQuantity = listing.remainingQuantity.round();
    if (_quantity == 0) {
      _quantity = maxQuantity >= 10 ? 10 : (maxQuantity > 0 ? maxQuantity : 0);
    }
    final total = _quantity * listing.pricePerUnit;

    return Scaffold(
      appBar: AppBar(title: AutoTranslatedText(listing.cropName)),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [

          Container(
            height: 160,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: const Color(0xFFF3F4F6),
              borderRadius: BorderRadius.circular(20),
            ),
            child: AutoTranslatedText(listing.emoji, style: const TextStyle(fontSize: 76)),
          ),
          const SizedBox(height: 16),

          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: AutoTranslatedText(
                  listing.cropName,
                  style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900),
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  AutoTranslatedText(
                    '₹${listing.pricePerUnit.round()}',
                    style: const TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.w900,
                      color: AppTheme.primaryGreen,
                    ),
                  ),
                  AutoTranslatedText(
                    '/${listing.unit}',
                    style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 14),

          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: Column(
              children: [
                SymbolRow(
                  symbol: '📦',
                  label: context.t('available'),
                  value: '${listing.remainingQuantity.round()} ${listing.unit}',
                ),
                SymbolRow(symbol: '📍', label: context.t('location'), value: listing.location),
                SymbolRow(symbol: '👨‍🌾', label: context.t('farmer'), value: listing.farmerName),
                SymbolRow(
                  symbol: listing.urgencySymbol,
                  label: context.t('sell_by'),
                  value: context.tf('days_left', ['${listing.daysLeft}']),
                ),
              ],
            ),
          ),

          if (listing.description.isNotEmpty) ...[
            const SizedBox(height: 14),
            AutoTranslatedText(
              listing.description,
              style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.4),
            ),
          ],
          const SizedBox(height: 20),

          SectionHeader(symbol: '⚖️', title: context.t('quantity')),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: Row(
              children: [
                _stepButton(
                  icon: Icons.remove,
                  onTap: () => setState(() {
                    _quantity = (_quantity - 10).clamp(1, maxQuantity);
                  }),
                ),
                Expanded(
                  child: AutoTranslatedText(
                    '$_quantity ${listing.unit}',
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                  ),
                ),
                _stepButton(
                  icon: Icons.add,
                  onTap: () => setState(() {
                    _quantity = (_quantity + 10).clamp(1, maxQuantity);
                  }),
                ),
              ],
            ),
          ),
          const SizedBox(height: 90),
        ],
      ),

      bottomNavigationBar: SafeArea(
        child: Container(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
          decoration: const BoxDecoration(
            color: Colors.white,
            border: Border(top: BorderSide(color: AppTheme.borderLight)),
          ),
          child: Row(
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  AutoTranslatedText(
                    context.t('total'),
                    style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                  ),
                  AutoTranslatedText(
                    formatRupees(total),
                    style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900),
                  ),
                ],
              ),
              const SizedBox(width: 16),
              Expanded(
                child: SizedBox(
                  height: 50,
                  child: ElevatedButton(
                    onPressed: maxQuantity <= 0 ? null : () => _buy(context, listing.id),
                    child: AutoTranslatedText(
                      context.t('buy_now'),
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _buy(BuildContext context, String listingId) {
    final auth = context.read<AuthProvider>();
    final rescue = context.read<RescueProvider>();
    final listing = rescue.byId(listingId);
    if (listing == null) return;

    AuthGuard.requireAuth(
      context: context,
      authProvider: auth,
      actionType: 'buy',
      cropId: listing.id,
      cropName: listing.cropName,
      actionReason: context.t('login_to_buy'),
      onAuthenticated: () async {
        final paid = await Navigator.of(context).push<bool>(
          MaterialPageRoute(
            builder: (_) => CheckoutScreen(
              title: listing.cropName,
              items: [
                CheckoutItem(
                  cropId: listing.id,
                  name: listing.cropName,
                  emoji: listing.emoji,
                  quantity: _quantity,
                  unit: listing.unit,
                  pricePerUnit: listing.pricePerUnit,
                  farmerName: listing.farmerName,
                  location: listing.location,
                ),
              ],
            ),
          ),
        );

        if (paid == true) {
          rescue.recordSale(listing.id, _quantity.toDouble());
          if (mounted) Navigator.of(context).pop();
        }
      },
    );
  }

  Widget _stepButton({required IconData icon, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        width: 44,
        height: 40,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: const Color(0xFFF3F4F6),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, size: 20),
      ),
    );
  }
}
