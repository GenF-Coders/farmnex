import 'dart:async';
import 'dart:math';

import '../../models/payment_model.dart';

abstract class PaymentGateway {

  String get displayName;

  Future<PaymentResult> charge({
    required PaymentIntent intent,
    required PaymentMethod method,
    Map<String, String> instrument = const {},
  });

  Future<PaymentResult> refund({
    required String transactionId,
    required double amount,
    required PaymentMethod method,
  });
}

class MockPaymentGateway implements PaymentGateway {
  final Random _random = Random();

  @override
  String get displayName => 'Razorpay Test Mode (Sandbox)';

  @override
  Future<PaymentResult> charge({
    required PaymentIntent intent,
    required PaymentMethod method,
    Map<String, String> instrument = const {},
  }) async {

    await Future<void>.delayed(const Duration(milliseconds: 1400));

    if (method == PaymentMethod.upi) {
      final vpa = instrument['vpa'] ?? '';
      if (!vpa.contains('@') || vpa.length < 5) {
        return PaymentResult.failure(
          method: method,
          amount: intent.amount,
          message: '⚠️ Invalid UPI ID. Example: 9823456789@ybl',
        );
      }
    }
    if (method == PaymentMethod.card) {
      final number = (instrument['number'] ?? '').replaceAll(' ', '');
      if (number.length < 12) {
        return PaymentResult.failure(
          method: method,
          amount: intent.amount,
          message: '⚠️ Card number looks incomplete.',
        );
      }
    }

    return PaymentResult(
      success: true,
      transactionId: _reference('BHF'),
      status: intent.useEscrow ? PaymentStatus.escrowHeld : PaymentStatus.success,
      method: method,
      amount: intent.amount,
      message: intent.useEscrow
          ? '🔒 ₹${intent.amount.toStringAsFixed(0)} held in escrow. Released to the farmer on delivery.'
          : '✅ ₹${intent.amount.toStringAsFixed(0)} paid.',
    );
  }

  @override
  Future<PaymentResult> refund({
    required String transactionId,
    required double amount,
    required PaymentMethod method,
  }) async {
    await Future<void>.delayed(const Duration(milliseconds: 900));
    return PaymentResult(
      success: true,
      transactionId: _reference('RFD'),
      status: PaymentStatus.refunded,
      method: method,
      amount: amount,
      message: '↩️ ₹${amount.toStringAsFixed(0)} refunded. Reaches your account in 3–5 working days.',
    );
  }

  String _reference(String prefix) {
    final stamp = DateTime.now().millisecondsSinceEpoch.toString().substring(5);
    return '$prefix$stamp${_random.nextInt(900) + 100}';
  }
}

class RazorpaySandboxGateway extends MockPaymentGateway {
  @override
  String get displayName => 'Razorpay Test Mode (Sandbox)';
}

class RazorpayGateway implements PaymentGateway {
  @override
  String get displayName => 'Razorpay';

  @override
  Future<PaymentResult> charge({
    required PaymentIntent intent,
    required PaymentMethod method,
    Map<String, String> instrument = const {},
  }) async {

    return PaymentResult.failure(
      method: method,
      amount: intent.amount,
      message: 'Razorpay live SDK is not enabled. Razorpay Test Mode sandbox is active for this build.',
    );
  }

  @override
  Future<PaymentResult> refund({
    required String transactionId,
    required double amount,
    required PaymentMethod method,
  }) async {

    return PaymentResult.failure(
      method: method,
      amount: amount,
      message: 'Razorpay refunds are issued from the backend.',
    );
  }
}
