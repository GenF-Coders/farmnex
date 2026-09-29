import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/payment_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/symbol_widgets.dart';

class CheckoutItem {
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

class CheckoutScreen extends StatefulWidget {
  final List<CheckoutItem> items;
  final String title;
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
  PaymentMethod _method = PaymentMethod.upi;
  bool _farmerDispatch = true;
  bool _applyWallet = false;
  String _deliveryCity = 'Pune';

  final _vpaController = TextEditingController(text: '9823456789@ybl');
  final _cardNumberController = TextEditingController(text: '4111 1111 1111 1111');
  final _cardExpiryController = TextEditingController(text: '12/28');
  final _cardCvvController = TextEditingController();
  String _bank = '🏦 State Bank of India';

  PaymentResult? _receipt;
  String? _error;

  static const List<String> _maharashtraCities = [
    'Pune',
    'Mumbai',
    'Navi Mumbai',
    'Thane',
    'Nagpur',
    'Nashik',
    'Chhatrapati Sambhajinagar',
    'Kolhapur',
    'Solapur',
    'Sangli',
    'Satara',
    'Latur',
    'Nanded',
    'Jalgaon',
    'Dhule',
    'Ahmednagar',
    'Amravati',
    'Akola',
    'Beed',
    'Buldhana',
    'Chandrapur',
    'Parbhani',
    'Osmanabad',
    'Ratnagiri',
    'Sindhudurg',
    'Wardha',
    'Yavatmal',
    'Washim',
    'Gondia',
    'Bhandara',
    'Palghar',
    'Raigad',
  ];

  static const List<String> _banks = [
    '🏦 State Bank of India',
    '🏦 HDFC Bank',
    '🏦 ICICI Bank',
    '🏦 Bank of Baroda',
    '🏦 Punjab National Bank',
    '🏦 Maharashtra Gramin Bank',
  ];

  @override
  void dispose() {
    _vpaController.dispose();
    _cardNumberController.dispose();
    _cardExpiryController.dispose();
    _cardCvvController.dispose();
    super.dispose();
  }

  double get _subtotal =>
      widget.items.fold<double>(0, (sum, i) => sum + i.lineTotal);

  double get _logisticsFee {
    if (!_farmerDispatch) return 0;
    final quintals = widget.items.fold<int>(0, (sum, i) => sum + i.quantity);
    return quintals * 38;
  }

  MoneyBreakdown _breakdown(PaymentProvider payments) {
    final base = MoneyBreakdown.forTrade(
      subtotal: _subtotal,
      logisticsFee: _logisticsFee,
    );
    if (!_applyWallet || _method == PaymentMethod.wallet) return base;
    return base.copyWith(walletApplied: payments.maxWalletApplicable(base.grossTotal));
  }

  Future<void> _pay() async {
    final payments = context.read<PaymentProvider>();
    final auth = context.read<AuthProvider>();
    final breakdown = _breakdown(payments);

    setState(() => _error = null);

    final intent = PaymentIntent(
      id: 'pi-${DateTime.now().millisecondsSinceEpoch}',
      orderId: 'ord-${DateTime.now().millisecondsSinceEpoch.toString().substring(7)}',
      title: widget.title,
      symbol: widget.items.isNotEmpty ? widget.items.first.emoji : '🧾',
      breakdown: breakdown,
      payerId: auth.user?.id ?? 'guest',
      payeeName: widget.items.isNotEmpty ? widget.items.first.farmerName : 'FarmNex',
      useEscrow: widget.useEscrow && _method != PaymentMethod.cod,
    );

    final result = await payments.pay(
      intent: intent,
      method: _method,
      instrument: {
        'vpa': _vpaController.text.trim(),
        'number': _cardNumberController.text.trim(),
        'expiry': _cardExpiryController.text.trim(),
        'bank': _bank,
      },
      buildOrder: (res) {
        final first = widget.items.first;
        return OrderRecord(
          id: intent.orderId,
          cropId: first.cropId,
          cropName: widget.items.length == 1
              ? first.name
              : '${first.name} +${widget.items.length - 1}',
          emoji: first.emoji,
          farmerName: first.farmerName,
          buyerName: auth.user?.name ?? 'Buyer',
          pickupLocation: first.location,
          dropLocation: _deliveryCity,
          quantity: widget.items.fold<int>(0, (s, i) => s + i.quantity).toDouble(),
          unit: first.unit,
          pricePerUnit: first.pricePerUnit,
          totalPaid: res.amount,
          method: _method,
          paymentStatus: res.status,
          placedAt: DateTime.now(),
          transactionId: res.transactionId,
        );
      },
    );

    if (!mounted) return;
    if (result.success) {
      setState(() => _receipt = result);
    } else {
      setState(() => _error = result.message);
    }
  }

  @override
  Widget build(BuildContext context) {
    final payments = context.watch<PaymentProvider>();
    final breakdown = _breakdown(payments);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            AutoTranslatedText('🔒', style: TextStyle(fontSize: 18)),
            const SizedBox(width: 8),
            AutoTranslatedText(_receipt == null ? widget.title : 'Receipt'),
          ],
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => Navigator.of(context).pop(_receipt != null),
        ),
      ),
      body: _receipt != null
          ? _buildReceipt(_receipt!)
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _buildItemsCard(),
                const SizedBox(height: 14),
                _buildDeliveryCard(),
                const SizedBox(height: 14),
                _buildWalletCard(payments, breakdown),
                const SizedBox(height: 14),
                _buildMethodCard(),
                const SizedBox(height: 14),
                _buildInstrumentCard(),
                const SizedBox(height: 14),
                _buildBillCard(breakdown),
                const SizedBox(height: 14),
                if (_error != null) _buildErrorBanner(),
                _buildTrustFooter(payments),
                const SizedBox(height: 90),
              ],
            ),
      bottomNavigationBar: _receipt != null
          ? null
          : _buildPayBar(payments, breakdown),
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
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(symbol: '🚚', title: 'Delivery'),
          DropdownButtonFormField<String>(
            value: _deliveryCity,
            decoration: const InputDecoration(
              labelText: 'Delivery city',
              prefixIcon: Icon(Icons.location_city_outlined),
            ),
            items: _maharashtraCities
                .map((city) => DropdownMenuItem<String>(value: city, child: AutoTranslatedText(city)))
                .toList(),
            onChanged: (city) => setState(() => _deliveryCity = city ?? _deliveryCity),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(
                child: _choice(
                  symbol: '🚛',
                  label: 'Farmer dispatch',
                  sub: '₹38/q freight',
                  selected: _farmerDispatch,
                  onTap: () => setState(() => _farmerDispatch = true),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _choice(
                  symbol: '🏭',
                  label: 'Self pickup',
                  sub: '₹0 freight',
                  selected: !_farmerDispatch,
                  onTap: () => setState(() => _farmerDispatch = false),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildWalletCard(PaymentProvider payments, MoneyBreakdown breakdown) {
    final disabled = _method == PaymentMethod.wallet || payments.walletBalance <= 0;
    return _card(
      child: Row(
        children: [
          AutoTranslatedText('👛', style: TextStyle(fontSize: 22)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(
                  'Wallet  ${formatRupees(payments.walletBalance)}',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                ),
                AutoTranslatedText(
                  disabled
                      ? (payments.walletBalance <= 0 ? '⚠️ Empty' : '✅ Paying fully by wallet')
                      : '➖ Apply ${formatRupees(payments.maxWalletApplicable(breakdown.grossTotal))}',
                  style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                ),
              ],
            ),
          ),
          Switch(
            value: _applyWallet && !disabled,
            onChanged: disabled ? null : (v) => setState(() => _applyWallet = v),
          ),
        ],
      ),
    );
  }

  Widget _buildMethodCard() {
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(symbol: '💳', title: 'Pay with'),
          ...PaymentMethod.values.map((m) {
            final selected = _method == m;
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: InkWell(
                onTap: () => setState(() {
                  _method = m;
                  _error = null;
                  if (m == PaymentMethod.wallet) _applyWallet = false;
                }),
                borderRadius: BorderRadius.circular(14),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
                  decoration: BoxDecoration(
                    color: selected ? AppTheme.primaryGreen.withValues(alpha: 0.07) : Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: selected ? AppTheme.primaryGreen : AppTheme.borderLight,
                      width: selected ? 1.6 : 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      AutoTranslatedText(m.symbol, style: const TextStyle(fontSize: 20)),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            AutoTranslatedText(m.label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                            AutoTranslatedText(m.hint, style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                          ],
                        ),
                      ),
                      Icon(
                        selected ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                        size: 20,
                        color: selected ? AppTheme.primaryGreen : AppTheme.borderLight,
                      ),
                    ],
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }

  Widget _buildInstrumentCard() {
    switch (_method) {
      case PaymentMethod.upi:
        return _card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(symbol: '📲', title: 'UPI ID'),
              TextField(
                controller: _vpaController,
                decoration: const InputDecoration(
                  hintText: 'name@bank',
                  prefixIcon: Icon(Icons.alternate_email),
                ),
              ),
              const SizedBox(height: 10),
              const Wrap(
                spacing: 8,
                runSpacing: 6,
                children: [
                  _AppChip(symbol: '🟢', name: 'GPay'),
                  _AppChip(symbol: '🟣', name: 'PhonePe'),
                  _AppChip(symbol: '🔵', name: 'Paytm'),
                  _AppChip(symbol: '🟠', name: 'BHIM'),
                ],
              ),
            ],
          ),
        );

      case PaymentMethod.card:
        return _card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(symbol: '💳', title: 'Card'),
              TextField(
                controller: _cardNumberController,
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9 ]'))],
                decoration: const InputDecoration(
                  hintText: '#### #### #### ####',
                  prefixIcon: Icon(Icons.credit_card),
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _cardExpiryController,
                      decoration: const InputDecoration(hintText: '📅 MM/YY'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      controller: _cardCvvController,
                      obscureText: true,
                      keyboardType: TextInputType.number,
                      maxLength: 4,
                      decoration: const InputDecoration(hintText: '🔑 CVV', counterText: ''),
                    ),
                  ),
                ],
              ),
            ],
          ),
        );

      case PaymentMethod.netbanking:
        return _card(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SectionHeader(symbol: '🏦', title: 'Bank'),
              DropdownButtonFormField<String>(
                value: _bank,
                isExpanded: true,
                items: _banks
                    .map((b) => DropdownMenuItem(
                          value: b,
                          child: AutoTranslatedText(b, style: const TextStyle(fontSize: 13)),
                        ))
                    .toList(),
                onChanged: (v) => setState(() => _bank = v ?? _bank),
              ),
            ],
          ),
        );

      case PaymentMethod.wallet:
        return _card(
          child: Row(
            children: [
              AutoTranslatedText('👛', style: TextStyle(fontSize: 22)),
              const SizedBox(width: 12),
              const Expanded(
                child: AutoTranslatedText(
                  'Full amount is debited from your FarmNex wallet. No gateway fee.',
                  style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                ),
              ),
            ],
          ),
        );

      case PaymentMethod.cod:
        return _card(
          child: Row(
            children: [
              AutoTranslatedText('💵', style: TextStyle(fontSize: 22)),
              const SizedBox(width: 12),
              const Expanded(
                child: AutoTranslatedText(
                  'Pay the driver at the mandi gate. 🔒 Escrow protection does not apply to cash orders.',
                  style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
                ),
              ),
            ],
          ),
        );
    }
  }

  Widget _buildBillCard(MoneyBreakdown breakdown) {
    return _card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SectionHeader(symbol: '🧾', title: 'Bill'),
          SymbolRow(symbol: '🌾', label: 'Produce value', value: formatRupees(breakdown.subtotal)),
          SymbolRow(symbol: '⚙️', label: 'Platform fee (1%)', value: formatRupees(breakdown.platformFee)),
          SymbolRow(symbol: '🧾', label: 'GST on fee (5%)', value: formatRupees(breakdown.gst)),
          SymbolRow(
            symbol: '🚚',
            label: 'Freight',
            value: breakdown.logisticsFee == 0 ? '₹0' : formatRupees(breakdown.logisticsFee),
          ),
          SymbolRow(symbol: '🤝', label: 'Farmer brokerage', value: '₹0  ✅'),
          if (breakdown.walletApplied > 0)
            SymbolRow(
              symbol: '👛',
              label: 'Wallet applied',
              value: '- ${formatRupees(breakdown.walletApplied)}',
              valueColor: AppTheme.primaryGreen,
            ),
          const Divider(height: 20),
          SymbolRow(
            symbol: '💰',
            label: 'Payable',
            value: formatRupees(breakdown.payable),
            bold: true,
            valueColor: AppTheme.primaryGreen,
          ),
          const SizedBox(height: 6),
          AutoTranslatedText(
            '🧑‍🌾 ➜ ${formatRupees(breakdown.farmerSettlement)} reaches the farmer (0% cut)',
            style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
          ),
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
          AutoTranslatedText('⚠️', style: TextStyle(fontSize: 18)),
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

  Widget _buildTrustFooter(PaymentProvider payments) {
    return Column(
      children: [
        const Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            AutoTranslatedText('🔒', style: TextStyle(fontSize: 13)),
            SizedBox(width: 6),
            AutoTranslatedText('🛡️', style: TextStyle(fontSize: 13)),
            SizedBox(width: 6),
            AutoTranslatedText('✅', style: TextStyle(fontSize: 13)),
            SizedBox(width: 8),
            AutoTranslatedText(
              'PCI-DSS • 256-bit TLS • Escrow protected',
              style: TextStyle(fontSize: 10.5, color: AppTheme.textMuted, fontWeight: FontWeight.w600),
            ),
          ],
        ),
        const SizedBox(height: 4),
        AutoTranslatedText(
          payments.gatewayName,
          style: const TextStyle(fontSize: 9.5, color: AppTheme.textMuted),
        ),
      ],
    );
  }

  Widget _buildPayBar(PaymentProvider payments, MoneyBreakdown breakdown) {
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
                AutoTranslatedText('💰', style: TextStyle(fontSize: 12)),
                AutoTranslatedText(
                  formatRupees(breakdown.payable),
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
                    : AutoTranslatedText(
                        '${_method.symbol}  ${_method == PaymentMethod.cod ? 'Confirm' : 'Pay'}  ➜',
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReceipt(PaymentResult result) {
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
            child: AutoTranslatedText(result.status.symbol, style: const TextStyle(fontSize: 44)),
          ),
        ),
        const SizedBox(height: 18),
        Center(
          child: AutoTranslatedText(
            formatRupees(result.amount),
            style: const TextStyle(fontSize: 34, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
          ),
        ),
        const SizedBox(height: 6),
        Center(
          child: AutoTranslatedText(
            result.message,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 12.5, color: AppTheme.textMuted, height: 1.4),
          ),
        ),
        const SizedBox(height: 24),
        _card(
          child: Column(
            children: [
              SymbolRow(symbol: '🆔', label: 'Txn ID', value: result.transactionId ?? '—'),
              SymbolRow(symbol: result.method.symbol, label: 'Method', value: result.method.label),
              SymbolRow(symbol: result.status.symbol, label: 'Status', value: result.status.label),
              SymbolRow(
                symbol: '🕐',
                label: 'Time',
                value: TimeOfDay.fromDateTime(result.completedAt).format(context),
              ),
              SymbolRow(symbol: '🚚', label: 'Delivery', value: _farmerDispatch ? 'Farmer dispatch • $_deliveryCity' : 'Self pickup • $_deliveryCity'),
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
                  'Money is released to the farmer only after delivery OTP is verified.',
                  style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Color(0xFF14532D)),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: () => Navigator.of(context).pop(true),
          child: AutoTranslatedText('✅  Done'),
        ),
      ],
    );
  }

  Widget _choice({
    required String symbol,
    required String label,
    required String sub,
    required bool selected,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 10),
        decoration: BoxDecoration(
          color: selected ? AppTheme.primaryGreen.withValues(alpha: 0.07) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: selected ? AppTheme.primaryGreen : AppTheme.borderLight,
            width: selected ? 1.6 : 1,
          ),
        ),
        child: Column(
          children: [
            AutoTranslatedText(symbol, style: const TextStyle(fontSize: 22)),
            const SizedBox(height: 6),
            AutoTranslatedText(label, style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800)),
            AutoTranslatedText(sub, style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
          ],
        ),
      ),
    );
  }
}

class _AppChip extends StatelessWidget {
  final String symbol;
  final String name;

  const _AppChip({required this.symbol, required this.name});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: AutoTranslatedText('$symbol $name', style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700)),
    );
  }
}
