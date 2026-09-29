
enum PaymentMethod {
  upi,
  card,
  netbanking,
  wallet,
  cod;

  String get symbol {
    switch (this) {
      case PaymentMethod.upi:
        return '📲';
      case PaymentMethod.card:
        return '💳';
      case PaymentMethod.netbanking:
        return '🏦';
      case PaymentMethod.wallet:
        return '👛';
      case PaymentMethod.cod:
        return '💵';
    }
  }

  String get label {
    switch (this) {
      case PaymentMethod.upi:
        return 'UPI';
      case PaymentMethod.card:
        return 'Card';
      case PaymentMethod.netbanking:
        return 'Net Banking';
      case PaymentMethod.wallet:
        return 'FarmNex Wallet';
      case PaymentMethod.cod:
        return 'Cash on Delivery';
    }
  }

  String get hint {
    switch (this) {
      case PaymentMethod.upi:
        return 'GPay • PhonePe • Paytm • BHIM';
      case PaymentMethod.card:
        return 'Visa • RuPay • Mastercard';
      case PaymentMethod.netbanking:
        return 'SBI • HDFC • ICICI • BoB +54';
      case PaymentMethod.wallet:
        return '₹ balance • instant • 0 fee';
      case PaymentMethod.cod:
        return '🚚 ➜ 💵  (mandi gate payment)';
    }
  }

  bool get isOnline => this != PaymentMethod.cod;

  static PaymentMethod fromString(String value) {
    return PaymentMethod.values.firstWhere(
      (m) => m.name == value.toLowerCase(),
      orElse: () => PaymentMethod.upi,
    );
  }
}

enum PaymentStatus {
  pending,
  processing,
  escrowHeld,
  released,
  success,
  failed,
  refunded;

  String get symbol {
    switch (this) {
      case PaymentStatus.pending:
        return '⏳';
      case PaymentStatus.processing:
        return '🔄';
      case PaymentStatus.escrowHeld:
        return '🔒';
      case PaymentStatus.released:
        return '✅';
      case PaymentStatus.success:
        return '✅';
      case PaymentStatus.failed:
        return '❌';
      case PaymentStatus.refunded:
        return '↩️';
    }
  }

  String get label {
    switch (this) {
      case PaymentStatus.pending:
        return 'Pending';
      case PaymentStatus.processing:
        return 'Processing';
      case PaymentStatus.escrowHeld:
        return 'In Escrow';
      case PaymentStatus.released:
        return 'Settled';
      case PaymentStatus.success:
        return 'Paid';
      case PaymentStatus.failed:
        return 'Failed';
      case PaymentStatus.refunded:
        return 'Refunded';
    }
  }

  static PaymentStatus fromString(String value) {
    return PaymentStatus.values.firstWhere(
      (s) => s.name.toLowerCase() == value.toLowerCase(),
      orElse: () => PaymentStatus.pending,
    );
  }
}

class MoneyBreakdown {
  final double subtotal;
  final double platformFee;
  final double gst;
  final double logisticsFee;
  final double walletApplied;

  const MoneyBreakdown({
    required this.subtotal,
    this.platformFee = 0,
    this.gst = 0,
    this.logisticsFee = 0,
    this.walletApplied = 0,
  });

  factory MoneyBreakdown.forTrade({
    required double subtotal,
    double logisticsFee = 0,
    double walletApplied = 0,
  }) {
    final fee = (subtotal * 0.01);
    return MoneyBreakdown(
      subtotal: subtotal,
      platformFee: fee,
      gst: fee * 0.05,
      logisticsFee: logisticsFee,
      walletApplied: walletApplied,
    );
  }

  double get grossTotal => subtotal + platformFee + gst + logisticsFee;

  double get payable {
    final net = grossTotal - walletApplied;
    return net < 0 ? 0 : net;
  }

  double get farmerSettlement => subtotal;

  MoneyBreakdown copyWith({double? walletApplied, double? logisticsFee}) {
    return MoneyBreakdown(
      subtotal: subtotal,
      platformFee: platformFee,
      gst: gst,
      logisticsFee: logisticsFee ?? this.logisticsFee,
      walletApplied: walletApplied ?? this.walletApplied,
    );
  }
}

class PaymentIntent {
  final String id;
  final String orderId;
  final String title;
  final String symbol;
  final MoneyBreakdown breakdown;
  final String payerId;
  final String payeeName;
  final bool useEscrow;

  const PaymentIntent({
    required this.id,
    required this.orderId,
    required this.title,
    required this.symbol,
    required this.breakdown,
    required this.payerId,
    required this.payeeName,
    this.useEscrow = true,
  });

  double get amount => breakdown.payable;

  Map<String, dynamic> toJson() => {
        'id': id,
        'order_id': orderId,
        'amount': amount,
        'use_escrow': useEscrow,
        'payer_id': payerId,
      };
}

class PaymentResult {
  final bool success;
  final String? transactionId;
  final PaymentStatus status;
  final String message;
  final PaymentMethod method;
  final double amount;
  final DateTime completedAt;

  PaymentResult({
    required this.success,
    required this.status,
    required this.message,
    required this.method,
    required this.amount,
    this.transactionId,
    DateTime? completedAt,
  }) : completedAt = completedAt ?? DateTime.now();

  factory PaymentResult.failure({
    required PaymentMethod method,
    required double amount,
    String message = 'Payment could not be completed. No money was deducted.',
  }) {
    return PaymentResult(
      success: false,
      status: PaymentStatus.failed,
      message: message,
      method: method,
      amount: amount,
    );
  }
}

class WalletTxn {
  final String id;
  final String symbol;
  final String title;
  final double amount;
  final DateTime timestamp;
  final PaymentStatus status;
  final String? referenceOrderId;

  const WalletTxn({
    required this.id,
    required this.symbol,
    required this.title,
    required this.amount,
    required this.timestamp,
    this.status = PaymentStatus.success,
    this.referenceOrderId,
  });

  bool get isCredit => amount >= 0;
}

class OrderRecord {
  final String id;
  final String cropId;
  final String cropName;
  final String emoji;
  final String farmerName;
  final String buyerName;
  final String pickupLocation;
  final String dropLocation;
  final double quantity;
  final String unit;
  final double pricePerUnit;
  final double totalPaid;
  final PaymentMethod method;
  final PaymentStatus paymentStatus;
  final String deliveryStatus;
  final String? transactionId;
  final DateTime placedAt;

  const OrderRecord({
    required this.id,
    required this.cropId,
    required this.cropName,
    required this.emoji,
    required this.farmerName,
    required this.buyerName,
    required this.quantity,
    required this.unit,
    required this.pricePerUnit,
    required this.totalPaid,
    required this.method,
    required this.paymentStatus,
    required this.placedAt,
    this.pickupLocation = '',
    this.dropLocation = '',
    this.deliveryStatus = 'awaiting_pickup',
    this.transactionId,
  });

  String get deliverySymbol {
    switch (deliveryStatus) {
      case 'in_transit':
        return '🚚';
      case 'delivered':
        return '📦';
      default:
        return '⏳';
    }
  }

  OrderRecord copyWith({
    PaymentStatus? paymentStatus,
    String? deliveryStatus,
    String? transactionId,
  }) {
    return OrderRecord(
      id: id,
      cropId: cropId,
      cropName: cropName,
      emoji: emoji,
      farmerName: farmerName,
      buyerName: buyerName,
      pickupLocation: pickupLocation,
      dropLocation: dropLocation,
      quantity: quantity,
      unit: unit,
      pricePerUnit: pricePerUnit,
      totalPaid: totalPaid,
      method: method,
      paymentStatus: paymentStatus ?? this.paymentStatus,
      deliveryStatus: deliveryStatus ?? this.deliveryStatus,
      transactionId: transactionId ?? this.transactionId,
      placedAt: placedAt,
    );
  }
}
