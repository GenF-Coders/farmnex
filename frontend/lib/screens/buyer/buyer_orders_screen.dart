import 'package:flutter/material.dart';
import '../../widgets/auto_translated_text.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/payment_model.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/symbol_widgets.dart';

class BuyerOrdersScreen extends StatelessWidget {
  final VoidCallback? onBrowse;

  const BuyerOrdersScreen({super.key, this.onBrowse});

  @override
  Widget build(BuildContext context) {
    final payments = context.watch<PaymentProvider>();
    final orders = payments.orders;

    if (orders.isEmpty) {
      return SymbolEmptyState(
        symbol: '📦',
        message: 'No orders yet.\nBuy a lot to start tracking 🔒 escrow here.',
        actionLabel: '🏪  Browse mandi',
        onAction: onBrowse,
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: SymbolStat(
                symbol: '🔒',
                value: formatRupeesShort(payments.moneyInEscrow),
                caption: 'In escrow',
                color: AppTheme.accentAmber,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '✅',
                value: formatRupeesShort(payments.lifetimeSettled),
                caption: 'Settled',
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '📦',
                value: '${orders.length}',
                caption: 'Orders',
                color: AppTheme.accentTeal,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        const SectionHeader(symbol: '🧾', title: 'My orders'),
        ...orders.map((order) => _OrderTile(order: order)),
        const SizedBox(height: 20),
      ],
    );
  }
}

class _OrderTile extends StatelessWidget {
  final OrderRecord order;

  const _OrderTile({required this.order});

  @override
  Widget build(BuildContext context) {
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
              AutoTranslatedText(order.emoji, style: const TextStyle(fontSize: 22)),
              const SizedBox(width: 8),
              Expanded(
                child: AutoTranslatedText(
                  order.cropName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800),
                ),
              ),
              StatusPill(
                symbol: order.paymentStatus.symbol,
                label: order.paymentStatus.label,
                color: order.paymentStatus == PaymentStatus.failed
                    ? AppTheme.alertRed
                    : order.paymentStatus == PaymentStatus.escrowHeld
                        ? AppTheme.accentAmber
                        : AppTheme.primaryGreen,
              ),
            ],
          ),
          const SizedBox(height: 8),
          SymbolRow(symbol: '🆔', label: 'Txn', value: order.transactionId ?? '—'),
          SymbolRow(symbol: '⚖️', label: 'Quantity', value: '${order.quantity.round()} ${order.unit}'),
          SymbolRow(symbol: order.method.symbol, label: 'Paid via', value: order.method.label),
          SymbolRow(
            symbol: '💰',
            label: 'Total',
            value: formatRupees(order.totalPaid),
            bold: true,
            valueColor: AppTheme.primaryGreen,
          ),
          const Divider(height: 18),
          _timeline(order.deliveryStatus),
        ],
      ),
    );
  }

  Widget _timeline(String status) {
    const steps = ['🧾', '🔒', '🚚', '📦'];
    const labels = ['Placed', 'Escrow', 'Transit', 'Delivered'];
    final reached = switch (status) {
      'in_transit' => 3,
      'delivered' => 4,
      _ => 2,
    };

    return Row(
      children: List.generate(steps.length, (i) {
        final done = i < reached;
        return Expanded(
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: Container(
                      height: 2,
                      color: i == 0
                          ? Colors.transparent
                          : (done ? AppTheme.primaryGreen : AppTheme.borderLight),
                    ),
                  ),
                  Opacity(
                    opacity: done ? 1 : 0.32,
                    child: AutoTranslatedText(steps[i], style: const TextStyle(fontSize: 16)),
                  ),
                  Expanded(
                    child: Container(
                      height: 2,
                      color: i == steps.length - 1
                          ? Colors.transparent
                          : (i + 1 < reached ? AppTheme.primaryGreen : AppTheme.borderLight),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 3),
              AutoTranslatedText(
                labels[i],
                style: TextStyle(
                  fontSize: 9,
                  fontWeight: FontWeight.w700,
                  color: done ? AppTheme.primaryGreen : AppTheme.textMuted,
                ),
              ),
            ],
          ),
        );
      }),
    );
  }
}
