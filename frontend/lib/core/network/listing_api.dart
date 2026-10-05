import 'package:dio/dio.dart';

import '../../models/listing_model.dart';
import '../config/api_config.dart';
import 'api_client.dart';

/// Product listings (the lots farmers sell). Identity comes from the login token, never the body.
class ListingApi {
  final Dio _dio = ApiClient().dio;

  /// Every live lot (market), or only the signed-in seller's own lots in any status (`mine`).
  Future<List<ListingModel>> list({bool mine = false}) async {
    final response = await _dio.get<dynamic>(
      ApiConfig.productListingsEndpoint,
      queryParameters: {'limit': 100, if (mine) 'mine': true},
    );
    final data = response.data as List<dynamic>;
    return data.map((e) => ListingModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<ListingModel> create({
    required String farmId,
    required String cropBatchId,
    required String title,
    String? description,
    required String listingType,
    required double price,
    required double quantity,
    required String unit,
  }) async {
    final response = await _dio.post<dynamic>(ApiConfig.productListingsEndpoint, data: {
      'farm_id': farmId,
      'crop_batch_id': cropBatchId,
      'title': title,
      if (description != null && description.isNotEmpty) 'description': description,
      'listing_type': listingType,
      'price': price.toString(),
      'quantity': quantity.toString(),
      'unit': unit,
    });
    return ListingModel.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ListingModel> updatePrice(String publicId, double price) async {
    final response = await _dio.patch<dynamic>(
      ApiConfig.productListingEndpoint(publicId),
      data: {'price': price.toString()},
    );
    return ListingModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// Closes the lot (the backend keeps the row).
  Future<void> close(String publicId) => _dio.delete<dynamic>(ApiConfig.productListingEndpoint(publicId));
}

/// A short message for the screen. Never shows the raw exception; the screen translates it.
String listingErrorMessage(Object error) {
  if (error is DioException) {
    final code = error.response?.statusCode;
    if (code == 401) return 'Please log in to continue.';
    if (code == 403) return 'Your account is not allowed to do this.';
    if (code == 404) return 'Not found. Pull down to refresh.';
    if (code == 409 || code == 400 || code == 422) {
      final detail = error.response?.data is Map ? (error.response!.data as Map)['detail'] : null;
      if (detail is String && detail.isNotEmpty) return detail;
      return 'Please check the details and try again.';
    }
    if (error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return 'Could not reach the server. Check your internet and try again.';
    }
  }
  return 'Something went wrong. Please try again.';
}
