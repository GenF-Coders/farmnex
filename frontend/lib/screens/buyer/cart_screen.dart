import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/cart_provider.dart';
import '../../widgets/symbol_widgets.dart';
import '../payment/checkout_screen.dart';

class CartScreen extends StatelessWidget {
  final VoidCallback? onBrowse;

  const CartScreen({super.key, this.onBrowse});

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartProvider>();

    if (cart.isEmpty) {
      return SymbolEmptyState(
        symbol: '🛒',
        message: 'Cart is empty.\nAdd produce lots from 🏪 Mandi.',
        actionLabel: '🏪  Browse mandi',
        onAction: onBrowse,
      );
    }

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              SectionHeader(
                symbol: '🛒',
                title: 'Cart',
                trailing: TextButton.icon(
                  onPressed: cart.clear,
                  icon: const Icon(Icons.delete_outline, size: 16),
                  label: AutoTranslatedText('🗑️', style: TextStyle(fontSize: 13)),
                ),
              ),
              ...cart.lines.map((line) => _CartTile(line: line)),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFFF0FDF4),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.2)),
                ),
                child: Column(
                  children: [
                    SymbolRow(symbol: '📦', label: 'Lots', value: '${cart.itemCount}'),
                    SymbolRow(symbol: '⚖️', label: 'Quantity', value: '${cart.totalQuantity} q'),
                    SymbolRow(
                      symbol: '💰',
                      label: 'Subtotal',
                      value: formatRupees(cart.subtotal),
                      bold: true,
                      valueColor: AppTheme.primaryGreen,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
            ],
          ),
        ),
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
            child: ElevatedButton(
              onPressed: () async {
                final paid = await Navigator.of(context).push<bool>(
                  MaterialPageRoute(
                    builder: (_) => CheckoutScreen(
                      title: 'Checkout',
                      items: cart.lines
                          .map((l) => CheckoutItem(
                                cropId: l.crop.id,
                                name: l.crop.name,
                                emoji: l.crop.emoji,
                                quantity: l.quantity,
                                unit: l.crop.unit,
                                pricePerUnit: l.crop.currentPrice,
                                farmerName: l.crop.farmerName,
                                location: l.crop.location,
                              ))
                          .toList(),
                    ),
                  ),
                );
                if (paid == true) cart.clear();
              },
              child: AutoTranslatedText('🔒  ${formatRupees(cart.subtotal)}   ➜   Checkout'),
            ),
          ),
        ),
      ],
    );
  }
}

class _CartTile extends StatelessWidget {
  final CartLine line;

  const _CartTile({required this.line});

  @override
  Widget build(BuildContext context) {
    final cart = context.read<CartProvider>();
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: const Color(0xFFF3F4F6),
              borderRadius: BorderRadius.circular(14),
            ),
            child: AutoTranslatedText(line.crop.emoji, style: const TextStyle(fontSize: 24)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(
                  line.crop.name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                ),
                AutoTranslatedText(
                  '🧑‍🌾 ${line.crop.farmerName}  •  📍 ${line.crop.location}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    _stepper(
                      symbol: '➖',
                      onTap: () => cart.setQuantity(line.crop.id, line.quantity - 10),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      child: AutoTranslatedText(
                        '${line.quantity} q',
                        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900),
                      ),
                    ),
                    _stepper(
                      symbol: '➕',
                      onTap: () => cart.setQuantity(line.crop.id, line.quantity + 10),
                    ),
                    const Spacer(),
                    AutoTranslatedText(
                      formatRupees(line.lineTotal),
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w900),
                    ),
                  ],
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: 'Remove',
            icon: AutoTranslatedText('🗑️', style: TextStyle(fontSize: 16)),
            onPressed: () => cart.remove(line.crop.id),
          ),
        ],
      ),
    );
  }

  Widget _stepper({required String symbol, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        width: 28,
        height: 28,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: const Color(0xFFF3F4F6),
          borderRadius: BorderRadius.circular(8),
        ),
        child: AutoTranslatedText(symbol, style: const TextStyle(fontSize: 12)),
      ),
    );
  }
}
