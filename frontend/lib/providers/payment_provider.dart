import 'package:flutter/material.dart';

import '../core/payments/payment_gateway.dart';
import '../models/payment_model.dart';

class PaymentProvider extends ChangeNotifier {
  PaymentProvider({PaymentGateway? gateway})
      : _gateway = gateway ?? RazorpaySandboxGateway();

  final PaymentGateway _gateway;

  double _walletBalance = 12450;
  bool _isProcessing = false;
  String? _lastError;
  PaymentResult? _lastResult;

  final List<OrderRecord> _orders = [];
  final List<WalletTxn> _ledger = [
    WalletTxn(
      id: 'txn-seed-1',
      symbol: '🌾',
      title: 'Wheat settlement • Indore APMC',
      amount: 36750,
      timestamp: DateTime.now().subtract(const Duration(days: 4)),
      status: PaymentStatus.released,
    ),
    WalletTxn(
      id: 'txn-seed-2',
      symbol: '🚚',
      title: 'Freight paid • Latur ➜ Pune',
      amount: -4200,
      timestamp: DateTime.now().subtract(const Duration(days: 2)),
    ),
    WalletTxn(
      id: 'txn-seed-3',
      symbol: '🏦',
      title: 'Bank withdrawal • SBI ••4412',
      amount: -20100,
      timestamp: DateTime.now().subtract(const Duration(days: 1)),
    ),
  ];

  String get gatewayName => _gateway.displayName;
  double get walletBalance => _walletBalance;
  bool get isProcessing => _isProcessing;
  String? get lastError => _lastError;
  PaymentResult? get lastResult => _lastResult;

  List<WalletTxn> get ledger =>
      List.unmodifiable(_ledger..sort((a, b) => b.timestamp.compareTo(a.timestamp)));

  List<OrderRecord> get orders => List.unmodifiable(_orders);

  List<OrderRecord> ordersForBuyer(String buyerName) =>
      _orders.where((o) => o.buyerName == buyerName).toList();

  List<OrderRecord> ordersForFarmer(String farmerName) =>
      _orders.where((o) => o.farmerName == farmerName).toList();

  double get moneyInEscrow => _orders
      .where((o) => o.paymentStatus == PaymentStatus.escrowHeld)
      .fold<double>(0, (sum, o) => sum + o.totalPaid);

  double get lifetimeSettled => _orders
      .where((o) => o.paymentStatus == PaymentStatus.released)
      .fold<double>(0, (sum, o) => sum + o.totalPaid);

  double maxWalletApplicable(double billTotal) =>
      _walletBalance < billTotal ? _walletBalance : billTotal;

  Future<PaymentResult> pay({
    required PaymentIntent intent,
    required PaymentMethod method,
    Map<String, String> instrument = const {},
    required OrderRecord Function(PaymentResult result) buildOrder,
  }) async {
    _isProcessing = true;
    _lastError = null;
    notifyListeners();

    PaymentResult result;

    if (method == PaymentMethod.wallet) {

      await Future<void>.delayed(const Duration(milliseconds: 700));
      if (_walletBalance + 0.001 < intent.amount) {
        result = PaymentResult.failure(
          method: method,
          amount: intent.amount,
          message: '⚠️ Wallet short by ₹${(intent.amount - _walletBalance).toStringAsFixed(0)}. Pick another method.',
        );
      } else {
        _walletBalance -= intent.amount;
        result = PaymentResult(
          success: true,
          transactionId: 'WLT${DateTime.now().millisecondsSinceEpoch.toString().substring(6)}',
          status: intent.useEscrow ? PaymentStatus.escrowHeld : PaymentStatus.success,
          method: method,
          amount: intent.amount,
          message: '👛 ₹${intent.amount.toStringAsFixed(0)} paid from wallet.',
        );
      }
    } else if (method == PaymentMethod.cod) {
      await Future<void>.delayed(const Duration(milliseconds: 500));
      result = PaymentResult(
        success: true,
        transactionId: 'COD${DateTime.now().millisecondsSinceEpoch.toString().substring(6)}',
        status: PaymentStatus.pending,
        method: method,
        amount: intent.amount,
        message: '💵 Pay ₹${intent.amount.toStringAsFixed(0)} at the mandi gate on delivery.',
      );
    } else {
      result = await _gateway.charge(
        intent: intent,
        method: method,
        instrument: instrument,
      );

      if (result.success && intent.breakdown.walletApplied > 0) {
        _walletBalance -= intent.breakdown.walletApplied;
      }
    }

    if (result.success) {
      final order = buildOrder(result);
      _orders.insert(0, order);
      _ledger.add(
        WalletTxn(
          id: result.transactionId ?? 'txn-${DateTime.now().millisecondsSinceEpoch}',
          symbol: method.symbol,
          title: '${order.emoji} ${order.cropName} • ${method.label}',
          amount: method == PaymentMethod.cod ? 0 : -result.amount,
          timestamp: result.completedAt,
          status: result.status,
          referenceOrderId: order.id,
        ),
      );
    } else {
      _lastError = result.message;
    }

    _lastResult = result;
    _isProcessing = false;
    notifyListeners();
    return result;
  }

  void releaseEscrow(String orderId) {
    final index = _orders.indexWhere((o) => o.id == orderId);
    if (index == -1) return;
    final order = _orders[index];
    if (order.paymentStatus != PaymentStatus.escrowHeld) return;

    _orders[index] = order.copyWith(
      paymentStatus: PaymentStatus.released,
      deliveryStatus: 'delivered',
    );
    _walletBalance += order.totalPaid;
    _ledger.add(
      WalletTxn(
        id: 'rel-${order.id}',
        symbol: '✅',
        title: '${order.emoji} Escrow released • ${order.cropName}',
        amount: order.totalPaid,
        timestamp: DateTime.now(),
        status: PaymentStatus.released,
        referenceOrderId: order.id,
      ),
    );
    notifyListeners();
  }

  Future<void> refundOrder(String orderId) async {
    final index = _orders.indexWhere((o) => o.id == orderId);
    if (index == -1) return;
    final order = _orders[index];

    final result = await _gateway.refund(
      transactionId: order.transactionId ?? order.id,
      amount: order.totalPaid,
      method: order.method,
    );
    if (!result.success) return;

    _orders[index] = order.copyWith(paymentStatus: PaymentStatus.refunded);
    _walletBalance += order.totalPaid;
    _ledger.add(
      WalletTxn(
        id: 'rfd-${order.id}',
        symbol: '↩️',
        title: '${order.emoji} Refund • ${order.cropName}',
        amount: order.totalPaid,
        timestamp: DateTime.now(),
        status: PaymentStatus.refunded,
        referenceOrderId: order.id,
      ),
    );
    notifyListeners();
  }

  void markInTransit(String orderId) {
    final index = _orders.indexWhere((o) => o.id == orderId);
    if (index == -1) return;
    _orders[index] = _orders[index].copyWith(deliveryStatus: 'in_transit');
    notifyListeners();
  }

  Future<bool> topUp(double amount, PaymentMethod method) async {
    if (amount <= 0) return false;
    _isProcessing = true;
    notifyListeners();

    final result = await _gateway.charge(
      intent: PaymentIntent(
        id: 'topup-${DateTime.now().millisecondsSinceEpoch}',
        orderId: '-',
        title: 'Wallet top-up',
        symbol: '👛',
        breakdown: MoneyBreakdown(subtotal: amount),
        payerId: 'self',
        payeeName: 'FarmNex Wallet',
        useEscrow: false,
      ),
      method: method,
      instrument: const {'vpa': 'demo@ybl', 'number': '4111111111111111'},
    );

    if (result.success) {
      _walletBalance += amount;
      _ledger.add(
        WalletTxn(
          id: result.transactionId ?? 'top-${DateTime.now().millisecondsSinceEpoch}',
          symbol: '➕',
          title: 'Wallet top-up • ${method.label}',
          amount: amount,
          timestamp: DateTime.now(),
        ),
      );
    } else {
      _lastError = result.message;
    }

    _isProcessing = false;
    notifyListeners();
    return result.success;
  }

  Future<bool> withdrawToBank(double amount) async {
    if (amount <= 0 || amount > _walletBalance) {
      _lastError = '⚠️ Amount exceeds wallet balance.';
      notifyListeners();
      return false;
    }
    _isProcessing = true;
    notifyListeners();
    await Future<void>.delayed(const Duration(milliseconds: 900));

    _walletBalance -= amount;
    _ledger.add(
      WalletTxn(
        id: 'wd-${DateTime.now().millisecondsSinceEpoch}',
        symbol: '🏦',
        title: 'Withdrawal to bank • IMPS',
        amount: -amount,
        timestamp: DateTime.now(),
      ),
    );
    _isProcessing = false;
    notifyListeners();
    return true;
  }

  void clearError() {
    _lastError = null;
    notifyListeners();
  }
}
