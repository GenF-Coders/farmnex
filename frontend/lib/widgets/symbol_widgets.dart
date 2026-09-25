import 'auto_translated_text.dart';
import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';

String formatRupees(num value) {
  final isNegative = value < 0;
  final sign = isNegative ? '-' : '';
  final digits = value.abs().round().toString();
  if (digits.length <= 3) return '$sign₹$digits';

  final last3 = digits.substring(digits.length - 3);
  var rest = digits.substring(0, digits.length - 3);

  final groups = <String>[];
  while (rest.length > 2) {
    groups.insert(0, rest.substring(rest.length - 2));
    rest = rest.substring(0, rest.length - 2);
  }
  if (rest.isNotEmpty) groups.insert(0, rest);

  return '$sign₹${groups.join(',')},$last3';
}

String formatRupeesShort(num value) {
  final abs = value.abs();
  if (abs >= 10000000) return '₹${(value / 10000000).toStringAsFixed(1)}Cr';
  if (abs >= 100000) return '₹${(value / 100000).toStringAsFixed(1)}L';
  if (abs >= 1000) return '₹${(value / 1000).toStringAsFixed(1)}k';
  return '₹${value.round()}';
}

class SymbolStat extends StatelessWidget {
  final String symbol;
  final String value;
  final String caption;
  final Color color;
  final VoidCallback? onTap;

  const SymbolStat({
    super.key,
    required this.symbol,
    required this.value,
    required this.caption,
    this.color = AppTheme.primaryGreen,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.07),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: color.withValues(alpha: 0.18)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            AutoTranslatedText(symbol, style: const TextStyle(fontSize: 22)),
            const SizedBox(height: 8),
            FittedBox(
              fit: BoxFit.scaleDown,
              alignment: Alignment.centerLeft,
              child: AutoTranslatedText(
                value,
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900, color: color),
              ),
            ),
            const SizedBox(height: 2),
            AutoTranslatedText(
              caption,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
            ),
          ],
        ),
      ),
    );
  }
}

class SymbolAction extends StatelessWidget {
  final String symbol;
  final String label;
  final Color color;
  final VoidCallback onTap;
  final String? badge;

  const SymbolAction({
    super.key,
    required this.symbol,
    required this.label,
    required this.onTap,
    this.color = AppTheme.primaryGreen,
    this.badge,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(18),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppTheme.borderLight),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Stack(
              clipBehavior: Clip.none,
              children: [
                Container(
                  width: 46,
                  height: 46,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: color.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: AutoTranslatedText(symbol, style: const TextStyle(fontSize: 22)),
                ),
                if (badge != null)
                  Positioned(
                    right: -6,
                    top: -4,
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: AppTheme.alertRed,
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: Colors.white, width: 1.5),
                      ),
                      child: AutoTranslatedText(
                        badge!,
                        style: const TextStyle(color: Colors.white, fontSize: 9, fontWeight: FontWeight.w900),
                      ),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            AutoTranslatedText(
              label,
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      ),
    );
  }
}

class StatusPill extends StatelessWidget {
  final String symbol;
  final String label;
  final Color color;

  const StatusPill({
    super.key,
    required this.symbol,
    required this.label,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.28)),
      ),
      child: AutoTranslatedText(
        '$symbol $label',
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: color),
      ),
    );
  }
}

class SectionHeader extends StatelessWidget {
  final String symbol;
  final String title;
  final Widget? trailing;

  const SectionHeader({
    super.key,
    required this.symbol,
    required this.title,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          AutoTranslatedText(symbol, style: const TextStyle(fontSize: 16)),
          const SizedBox(width: 7),
          Expanded(
            child: AutoTranslatedText(
              title.toUpperCase(),
              style: const TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.5,
                color: AppTheme.textDark,
              ),
            ),
          ),
          if (trailing != null) trailing!,
        ],
      ),
    );
  }
}

class SymbolEmptyState extends StatelessWidget {
  final String symbol;
  final String message;
  final String? actionLabel;
  final VoidCallback? onAction;

  const SymbolEmptyState({
    super.key,
    required this.symbol,
    required this.message,
    this.actionLabel,
    this.onAction,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 48, horizontal: 24),
      child: Column(
        children: [
          AutoTranslatedText(symbol, style: const TextStyle(fontSize: 52)),
          const SizedBox(height: 12),
          AutoTranslatedText(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
          ),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: 16),
            SizedBox(
              width: 200,
              child: ElevatedButton(onPressed: onAction, child: AutoTranslatedText(actionLabel!)),
            ),
          ],
        ],
      ),
    );
  }
}

class SymbolRow extends StatelessWidget {
  final String symbol;
  final String label;
  final String value;
  final Color? valueColor;
  final bool bold;

  const SymbolRow({
    super.key,
    required this.symbol,
    required this.label,
    required this.value,
    this.valueColor,
    this.bold = false,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          AutoTranslatedText(symbol, style: const TextStyle(fontSize: 13)),
          const SizedBox(width: 8),
          Expanded(
            child: AutoTranslatedText(
              label,
              style: TextStyle(
                fontSize: 12,
                color: bold ? AppTheme.textDark : AppTheme.textMuted,
                fontWeight: bold ? FontWeight.w800 : FontWeight.w500,
              ),
            ),
          ),
          AutoTranslatedText(
            value,
            style: TextStyle(
              fontSize: bold ? 14 : 12.5,
              fontWeight: bold ? FontWeight.w900 : FontWeight.w700,
              color: valueColor ?? AppTheme.textDark,
            ),
          ),
        ],
      ),
    );
  }
}
