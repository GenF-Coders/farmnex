import 'package:flutter/material.dart';
import 'auto_translated_text.dart';
import '../core/theme/app_theme.dart';

class _TrustBadge {
  final IconData icon;
  final String label;
  const _TrustBadge(this.icon, this.label);
}

class TrustBadgeStrip extends StatelessWidget {
  const TrustBadgeStrip({super.key});

  static const _badges = [
    _TrustBadge(Icons.verified_user_rounded, 'Verified\nFarmers'),
    _TrustBadge(Icons.storefront_rounded, 'Direct Mandi\nPrices'),
    _TrustBadge(Icons.lock_outline_rounded, 'Secure\nPayments'),
    _TrustBadge(Icons.local_shipping_outlined, 'Pan-India\nLogistics'),
  ];

  @override
  Widget build(BuildContext context) {
    return Row(
      children: _badges
          .map(
            (b) => Expanded(
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen.withValues(alpha: 0.08),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(b.icon, color: AppTheme.primaryGreen, size: 18),
                  ),
                  const SizedBox(height: 6),
                  AutoTranslatedText(
                    b.label,
                    textAlign: TextAlign.center,
                    style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppTheme.textMuted, height: 1.2),
                  ),
                ],
              ),
            ),
          )
          .toList(),
    );
  }
}
