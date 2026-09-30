import 'package:flutter_test/flutter_test.dart';
import 'package:farmnex_flutter/models/order_model.dart';
import 'package:farmnex_flutter/providers/payment_provider.dart';

void main() {
  test('OrderModel reads the server JSON and works out what the buyer can do', () {
    final order = OrderModel.fromJson({
      'public_id': 'o-1',
      'order_number': 'FN-1-A',
      'status': 'PLACED',
      'subtotal': '1000.00',
      'delivery_fee': '50.00',
      'total_amount': '1050.00',
      'delivery_address_snapshot': {'city': 'Pune'},
    });
    expect(order.total, 1050);
    expect(order.deliveryCity, 'Pune');
    expect(order.canPay, isTrue);
    expect(order.canTrack, isFalse);

    final paid = order.withDetails(lines: const [], paymentStatus: 'HELD');
    expect(paid.canPay, isFalse);
    expect(paid.isPaid, isTrue);
  });

  test('WalletSummary reads amounts and entries', () {
    final wallet = WalletSummary.fromJson({
      'held_from_me': '200.00',
      'held_for_me': '0',
      'received': '50',
      'refunded': '0',
      'entries': [
        {'public_id': 'e-1', 'entry_type': 'HOLD', 'amount': '200.00', 'order_id': 'o-1'},
      ],
    });
    expect(wallet.heldFromMe, 200);
    expect(wallet.entries.single.isCredit, isFalse);
  });

  test('PaymentProvider starts empty and releaseEscrow does nothing', () {
    final provider = PaymentProvider();
    expect(provider.orders, isEmpty);
    expect(provider.walletBalance, 0);
    provider.releaseEscrow('o-1');
    expect(provider.moneyInEscrow, 0);
  });
}
