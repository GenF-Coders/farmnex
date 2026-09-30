import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/order_model.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/symbol_widgets.dart';

class CheckoutItem {
  /// The listing's public id (the id the market uses for a lot).
  final String cropId;
  final String name;
  final String emoji;
  final int quantity;
  final String unit;
  final double pricePerUnit;
  final String farmerName;
  final String location;

  const CheckoutItem({
    required this.cropId,
    required this.name,
    required this.emoji,
    required this.quantity,
    required this.unit,
    required this.pricePerUnit,
    required this.farmerName,
    required this.location,
  });

  double get lineTotal => pricePerUnit * quantity;
}

/// Checkout = 1) the server turns the items into orders (one per farmer), 2) Pay (demo) on each.
/// No real money moves. If step 2 fails the orders stay saved and the button only retries the
/// payment, so nothing is ordered twice.
class CheckoutScreen extends StatefulWidget {
  final List<CheckoutItem> items;
  final String title;

  /// Kept so existing callers compile; the server always holds the money until delivery.
  final bool useEscrow;

  const CheckoutScreen({
    super.key,
    required this.items,
    this.title = 'Checkout',
    this.useEscrow = true,
  });

  @override
  State<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends State<CheckoutScreen> {
  List<OrderModel>? _orders;
  final Map<String, PaymentReceipt> _receipts = {};
  String? _error;

  bool get _allPaid => _orders != null && _orders!.every((o) => _receipts.containsKey(o.publicId));

  double get _estimate => widget.items.fold<double>(0, (sum, i) => sum + i.lineTotal);

  double get _payable => _orders == null ? _estimate : _orders!.fold<double>(0, (sum, o) => sum + o.total);

  Future<void> _pay() async {
    final payments = context.read<PaymentProvider>();
    setState(() => _error = null);

    if (_orders == null) {
      final placed = await payments.placeOrders([
        for (final i in widget.items) (listingId: i.cropId, quantity: i.quantity),
      ]);
      if (!mounted) return;
      if (placed == null) {
        setState(() => _error = payments.lastError ?? 'Something went wrong. Please try again.');
        return;
      }
      setState(() => _orders = placed);
    }

    for (final order in _orders!) {
      if (_receipts.containsKey(order.publicId)) continue;
      final receipt = await payments.payOrder(order.publicId);
      if (!mounted) return;
      if (receipt == null) {
        setState(() => _error = payments.lastError ?? 'Payment did not go through. Please try again.');
        return;
      }
      setState(() => _receipts[order.publicId] = receipt);
    }
    payments.load(keepOld: true);
  }

  @override
  Widget build(BuildContext context) {
    final payments = context.watch<PaymentProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const AutoTranslatedText('🔒', style: TextStyle(fontSize: 18)),
            const SizedBox(width: 8),
            AutoTranslatedText(_allPaid ? 'Receipt' : widget.title),
          ],
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          // true once orders exist, so the cart is emptied and a retry can't order twice.
          onPressed: () => Navigator.of(context).pop(_orders != null),
        ),
      ),
      body: _allPaid
          ? _buildReceipt()
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildItemsCard(),
                const SizedBox(height: 14),
                _buildDeliveryCard(),
                const SizedBox(height: 14),
                _buildBillCard(),
                const SizedBox(height: 14),
                if (_error != null) _buildErrorBanner(),
                const AutoTranslatedText(
                  'Pay (demo): no real money moves. The amount is held by FarmNex and paid to the farmer only after delivery.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 10.5, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 90),
              ],
            ),
      bottomNavigationBar: _allPaid ? null : _buildPayBar(payments),
    );
  }

  Widget _card({required Widget child}) => Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppTheme.borderLight),
        ),
        child: child,
      );

  Widget _buildItemsCard() {
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(symbol: '🧺', title: 'Order'),
          ...widget.items.map(
            (item) => Padding(
              padding: const EdgeInsets.only(bottom: 10),
              child: Row(
                children: [
                  Container(
                    width: 42,
                    height: 42,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: const Color(0xFFF3F4F6),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: AutoTranslatedText(item.emoji, style: const TextStyle(fontSize: 20)),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AutoTranslatedText(
                          item.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                        ),
                        AutoTranslatedText(
                          '🧑‍🌾 ${item.farmerName}  •  📍 ${item.location}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                        ),
                        AutoTranslatedText(
                          '⚖️ ${item.quantity} ${item.unit}  ×  ₹${item.pricePerUnit.round()}',
                          style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                        ),
                      ],
                    ),
                  ),
                  AutoTranslatedText(
                    formatRupees(item.lineTotal),
                    style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w900),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDeliveryCard() {
    return _card(
      child: const Row(
        children: [
          AutoTranslatedText('🚚', style: TextStyle(fontSize: 22)),
          SizedBox(width: 12),
          Expanded(
            child: AutoTranslatedText(
              'Delivered to your default address.',
              style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBillCard() {
    final orders = _orders;
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(symbol: '🧾', title: 'Bill'),
          if (orders == null) ...[
            SymbolRow(symbol: '🌾', label: 'Produce value', value: formatRupees(_estimate)),
            const AutoTranslatedText(
              'Delivery and the final total are worked out by FarmNex when you place the order.',
              style: TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
            ),
          ] else ...[
            for (final o in orders) ...[
              SymbolRow(symbol: '🧾', label: 'Order ${o.orderNumber}', value: formatRupees(o.total)),
              if (o.deliveryFee > 0)
                SymbolRow(symbol: '🚚', label: 'Delivery fee', value: formatRupees(o.deliveryFee)),
            ],
            const Divider(height: 20),
            SymbolRow(
              symbol: '💰',
              label: 'To pay',
              value: formatRupees(_payable),
              bold: true,
              valueColor: AppTheme.primaryGreen,
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildErrorBanner() {
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppTheme.alertRed.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.alertRed.withValues(alpha: 0.3)),
      ),
      child: Row(
        children: [
          const AutoTranslatedText('⚠️', style: TextStyle(fontSize: 18)),
          const SizedBox(width: 10),
          Expanded(
            child: AutoTranslatedText(
              _error!,
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.alertRed),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPayBar(PaymentProvider payments) {
    return SafeArea(
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
                const AutoTranslatedText('💰', style: TextStyle(fontSize: 12)),
                AutoTranslatedText(
                  formatRupees(_payable),
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900),
                ),
              ],
            ),
            const SizedBox(width: 16),
            Expanded(
              child: ElevatedButton(
                onPressed: payments.isProcessing ? null : _pay,
                child: payments.isProcessing
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const AutoTranslatedText(
                        '🔒  Pay (demo)  ➜',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReceipt() {
    final total = _receipts.values.fold<double>(0, (sum, r) => sum + r.amount);
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const SizedBox(height: 20),
        Center(
          child: Container(
            width: 96,
            height: 96,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppTheme.primaryGreen.withValues(alpha: 0.1),
              shape: BoxShape.circle,
            ),
            child: const AutoTranslatedText('🔒', style: TextStyle(fontSize: 44)),
          ),
        ),
        const SizedBox(height: 18),
        Center(
          child: AutoTranslatedText(
            formatRupees(total),
            style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
          ),
        ),
        const SizedBox(height: 6),
        const Center(
          child: AutoTranslatedText(
            'Paid (demo). No real money moved. The amount is held until your order is delivered.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12.5, color: AppTheme.textMuted, height: 1.4),
          ),
        ),
        const SizedBox(height: 24),
        _card(
          child: Column(
            children: [
              for (final o in _orders!)
                SymbolRow(
                  symbol: '🧾',
                  label: o.orderNumber,
                  value: '${formatRupees(_receipts[o.publicId]!.amount)}  •  Held',
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
            border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.25)),
          ),
          child: const Row(
            children: [
              AutoTranslatedText('🔒 ➜ 🚚 ➜ 📦 ➜ ✅', style: TextStyle(fontSize: 16)),
              SizedBox(width: 10),
              Expanded(
                child: AutoTranslatedText(
                  'Money is released to the farmer only after the driver marks the order delivered.',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF14532D)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: const AutoTranslatedText('✅  Done'),
        ),
      ],
    );
  }
}
