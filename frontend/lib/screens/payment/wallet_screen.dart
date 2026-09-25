import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/payment_model.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/symbol_widgets.dart';

class WalletScreen extends StatelessWidget {
  final bool asTab;

  const WalletScreen({super.key, this.asTab = true});

  @override
  Widget build(BuildContext context) {
    final payments = context.watch<PaymentProvider>();
    final body = _buildBody(context, payments);

    if (asTab) return body;
    return Scaffold(
      appBar: AppBar(title: AutoTranslatedText('👛  Wallet')),
      body: body,
    );
  }

  Widget _buildBody(BuildContext context, PaymentProvider payments) {
    return ListView(
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
                    'Balance',
                    style: TextStyle(fontSize: 12, color: Color(0xFFBBF7D0), fontWeight: FontWeight.w700),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              AutoTranslatedText(
                formatRupees(payments.walletBalance),
                style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: _heroStat('🔒', formatRupeesShort(payments.moneyInEscrow), 'In escrow'),
                  ),
                  Container(width: 1, height: 32, color: Colors.white24),
                  Expanded(
                    child: _heroStat('✅', formatRupeesShort(payments.lifetimeSettled), 'Settled'),
                  ),
                  Container(width: 1, height: 32, color: Colors.white24),
                  Expanded(
                    child: _heroStat('📦', '${payments.orders.length}', 'Orders'),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        Row(
          children: [
            Expanded(
              child: SymbolAction(
                symbol: '➕',
                label: 'Top-up',
                onTap: () => _showTopUpSheet(context, payments),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolAction(
                symbol: '🏦',
                label: 'Withdraw',
                color: AppTheme.accentTeal,
                onTap: () => _showWithdrawSheet(context, payments),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolAction(
                symbol: '📄',
                label: 'Statement',
                color: AppTheme.accentAmber,
                onTap: () => ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: AutoTranslatedText('📧 Statement emailed as PDF.')),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        const SectionHeader(symbol: '📜', title: 'Ledger'),
        ...payments.ledger.map((txn) => _txnTile(txn)),
        const SizedBox(height: 20),
      ],
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

  Widget _txnTile(WalletTxn txn) {
    final credit = txn.isCredit;
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
              color: (credit ? AppTheme.primaryGreen : AppTheme.alertRed).withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(12),
            ),
            child: AutoTranslatedText(txn.symbol, style: const TextStyle(fontSize: 18)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(
                  txn.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700),
                ),
                AutoTranslatedText(
                  '${txn.status.symbol} ${_ago(txn.timestamp)}',
                  style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                ),
              ],
            ),
          ),
          AutoTranslatedText(
            '${credit ? '➕' : '➖'} ${formatRupees(txn.amount.abs())}',
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

  void _showTopUpSheet(BuildContext context, PaymentProvider payments) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => _AmountSheet(
        symbol: '➕',
        title: 'Top-up wallet',
        confirmLabel: '📲  Pay',
        presets: const [1000, 5000, 10000, 25000],
        onConfirm: (amount) async {
          final ok = await payments.topUp(amount, PaymentMethod.upi);
          return ok
              ? '✅ ${formatRupees(amount)} added.'
              : (payments.lastError ?? '❌ Top-up failed.');
        },
      ),
    );
  }

  void _showWithdrawSheet(BuildContext context, PaymentProvider payments) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => _AmountSheet(
        symbol: '🏦',
        title: 'Withdraw to bank',
        confirmLabel: '🏦  Withdraw',
        presets: const [2000, 10000, 20000],
        onConfirm: (amount) async {
          final ok = await payments.withdrawToBank(amount);
          return ok
              ? '✅ ${formatRupees(amount)} sent via IMPS.'
              : (payments.lastError ?? '❌ Withdrawal failed.');
        },
      ),
    );
  }
}

class _AmountSheet extends StatefulWidget {
  final String symbol;
  final String title;
  final String confirmLabel;
  final List<double> presets;
  final Future<String> Function(double amount) onConfirm;

  const _AmountSheet({
    required this.symbol,
    required this.title,
    required this.confirmLabel,
    required this.presets,
    required this.onConfirm,
  });

  @override
  State<_AmountSheet> createState() => _AmountSheetState();
}

class _AmountSheetState extends State<_AmountSheet> {
  final _controller = TextEditingController(text: '5000');
  bool _busy = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final amount = double.tryParse(_controller.text.trim()) ?? 0;
    if (amount <= 0) return;
    setState(() => _busy = true);
    final message = await widget.onConfirm(amount);
    if (!mounted) return;
    setState(() => _busy = false);
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: AutoTranslatedText(message)));
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              AutoTranslatedText(widget.symbol, style: const TextStyle(fontSize: 22)),
              const SizedBox(width: 10),
              AutoTranslatedText(widget.title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _controller,
            keyboardType: TextInputType.number,
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w900),
            decoration: const InputDecoration(prefixText: '₹ '),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: widget.presets
                .map((p) => ActionChip(
                      label: AutoTranslatedText('₹${p.round()}'),
                      onPressed: () => setState(() => _controller.text = p.round().toString()),
                    ))
                .toList(),
          ),
          const SizedBox(height: 18),
          ElevatedButton(
            onPressed: _busy ? null : _submit,
            child: _busy
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                  )
                : AutoTranslatedText(widget.confirmLabel),
          ),
        ],
      ),
    );
  }
}
