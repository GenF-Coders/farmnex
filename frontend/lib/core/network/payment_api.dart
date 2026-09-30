import 'package:dio/dio.dart';

import '../../models/order_model.dart';
import '../config/api_config.dart';
import 'api_client.dart';
import 'listing_api.dart' show listingErrorMessage;

/// Pay (demo) and the wallet. No real money moves; the server works out the amount, holds it until
/// delivery and releases it to the farmer. The app never sends an amount, payer or status.
class PaymentApi {
  final Dio _dio = ApiClient().dio;

  /// Paying the same order again returns the same payment, so a double tap cannot charge twice.
  Future<PaymentReceipt> payDemo(String orderId, {required String idempotencyKey}) async {
    final response = await _dio.post<dynamic>(
      ApiConfig.payDemoEndpoint(orderId),
      options: Options(headers: {'Idempotency-Key': idempotencyKey}),
    );
    return PaymentReceipt.fromJson(response.data as Map<String, dynamic>);
  }

  /// My payments (as buyer).
  Future<List<PaymentReceipt>> list() async {
    final response = await _dio.get<dynamic>(ApiConfig.paymentsEndpoint, queryParameters: {'limit': 100});
    return (response.data as List<dynamic>).map((e) => PaymentReceipt.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<WalletSummary> wallet() async {
    final response = await _dio.get<dynamic>(ApiConfig.walletEndpoint);
    return WalletSummary.fromJson(response.data as Map<String, dynamic>);
  }
}

String paymentErrorMessage(Object error) => listingErrorMessage(error);
