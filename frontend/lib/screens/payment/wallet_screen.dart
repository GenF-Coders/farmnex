import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/order_model.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/symbol_widgets.dart';

/// The demo wallet: money held for deliveries, money released to me and refunds, straight from the
/// server's ledger. There is no Top up or Withdraw: no real money moves in this prototype.
class WalletScreen extends StatefulWidget {
  final bool asTab;

  const WalletScreen({super.key, this.asTab = true});

  @override
  State<WalletScreen> createState() => _WalletScreenState();
}

class _WalletScreenState extends State<WalletScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<PaymentProvider>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final payments = context.watch<PaymentProvider>();
    final body = _buildBody(context, payments);

    if (widget.asTab) return body;
    return Scaffold(
      appBar: AppBar(title: const AutoTranslatedText('👛  Wallet')),
      body: body,
    );
  }

  Widget _buildBody(BuildContext context, PaymentProvider payments) {
    if (payments.isLoading && payments.wallet.entries.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (payments.lastError != null && payments.wallet.entries.isEmpty) {
      return SymbolEmptyState(
        symbol: '⚠️',
        message: payments.lastError!,
        actionLabel: '🔄  Try again',
        onAction: () => payments.load(),
      );
    }

    final wallet = payments.wallet;
    return RefreshIndicator(
      onRefresh: () => payments.load(keepOld: true),
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF166534), Color(0xFF0F766E)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              borderRadius: BorderRadius.circular(22),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    AutoTranslatedText('👛', style: TextStyle(fontSize: 20)),
                    SizedBox(width: 8),
                    AutoTranslatedText(
                      'Received (demo)',
                      style: TextStyle(fontSize: 12, color: Color(0xFFBBF7D0), fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                AutoTranslatedText(
                  formatRupees(wallet.received),
                  style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w900, color: Colors.white),
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(child: _heroStat('🔒', formatRupeesShort(wallet.heldFromMe), 'You paid, held')),
                    Container(width: 1, height: 32, color: Colors.white24),
                    Expanded(child: _heroStat('🌾', formatRupeesShort(wallet.heldForMe), 'Held for you')),
                    Container(width: 1, height: 32, color: Colors.white24),
                    Expanded(child: _heroStat('↩️', formatRupeesShort(wallet.refunded), 'Refunded')),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 10),
          const AutoTranslatedText(
            'Demo wallet: no real money moves. Money is held until an order is delivered, then paid to the farmer.',
            style: TextStyle(fontSize: 10.5, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 20),
          const SectionHeader(symbol: '📜', title: 'Ledger'),
          if (wallet.entries.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 16),
              child: AutoTranslatedText(
                'Nothing yet. Payments and releases will appear here.',
                style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
              ),
            ),
          ...wallet.entries.map((entry) => _entryTile(payments, entry)),
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _heroStat(String symbol, String value, String caption) {
    return Column(
      children: [
        AutoTranslatedText(symbol, style: const TextStyle(fontSize: 14)),
        const SizedBox(height: 2),
        AutoTranslatedText(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: Colors.white)),
        AutoTranslatedText(caption, style: const TextStyle(fontSize: 9.5, color: Color(0xFFBBF7D0))),
      ],
    );
  }

  static String _entryTitle(WalletEntry entry, String orderNumber) {
    final order = orderNumber.isEmpty ? '' : ' • $orderNumber';
    switch (entry.type) {
      case 'HOLD':
        return 'Held for delivery$order';
      case 'RELEASE':
        return 'Paid out on delivery$order';
      case 'REFUND':
        return 'Refund$order';
      default:
        return '${entry.type}$order';
    }
  }

  static String _entrySymbol(String type) {
    switch (type) {
      case 'HOLD':
        return '🔒';
      case 'RELEASE':
        return '✅';
      case 'REFUND':
        return '↩️';
      default:
        return '🧾';
    }
  }

  Widget _entryTile(PaymentProvider payments, WalletEntry entry) {
    final credit = entry.isCredit;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: (credit ? AppTheme.primaryGreen : AppTheme.accentAmber).withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
            ),
            child: AutoTranslatedText(_entrySymbol(entry.type), style: const TextStyle(fontSize: 18)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(
                  _entryTitle(entry, payments.orderNumberFor(entry.orderId)),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700),
                ),
                if (entry.createdAt != null)
                  AutoTranslatedText(
                    _ago(entry.createdAt!),
                    style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                  ),
              ],
            ),
          ),
          AutoTranslatedText(
            '${credit ? '➕' : '➖'} ${formatRupees(entry.amount)}',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w900,
              color: credit ? AppTheme.primaryGreen : AppTheme.textDark,
            ),
          ),
        ],
      ),
    );
  }

  static String _ago(DateTime time) {
    final diff = DateTime.now().difference(time);
    if (diff.inMinutes < 1) return 'just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes} min';
    if (diff.inHours < 24) return '${diff.inHours} hr';
    return '${diff.inDays} d';
  }
}
