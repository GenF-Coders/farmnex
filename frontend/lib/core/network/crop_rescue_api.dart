import 'package:dio/dio.dart';

import '../../models/rescue_listing_model.dart';
import '../config/api_config.dart';
import 'api_client.dart';

/// Crop Rescue calls (`/api/v2/rescue/...`). Only farmers may use them. The farmer comes from the
/// login token, so no farmer id is ever sent.
class CropRescueApi {
  final Dio _dio;

  CropRescueApi([Dio? dio]) : _dio = dio ?? ApiClient().dio;

  Future<List<RescueCrop>> crops() async {
    final response = await _dio.get<dynamic>(ApiConfig.rescueCropsEndpoint);
    final list = (response.data as Map<String, dynamic>)['crops'] as List<dynamic>;
    return list.map((e) => RescueCrop.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<RescueLot>> lots() async {
    final response = await _dio.get<dynamic>(ApiConfig.rescueLotsEndpoint);
    return (response.data as List<dynamic>)
        .map((e) => RescueLot.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RescueLot> lot(String id) async {
    final response = await _dio.get<dynamic>(ApiConfig.rescueLotEndpoint(id));
    return RescueLot.fromJson(response.data as Map<String, dynamic>);
  }

  Future<RescueLot> createLot({
    required String cropCode,
    required double quantityKg,
    required DateTime harvestedAt,
    required double lat,
    required double lng,
    String storageMode = 'ambient',
    double floorPricePerKg = 0,
  }) async {
    final response = await _dio.post<dynamic>(ApiConfig.rescueLotsEndpoint, data: {
      'crop_code': cropCode,
      'quantity_kg': quantityKg,
      'harvested_at': harvestedAt.toUtc().toIso8601String(),
      'lat': lat,
      'lng': lng,
      'storage_mode': storageMode,
      'floor_price_per_kg': floorPricePerKg,
    });
    return RescueLot.fromJson(response.data as Map<String, dynamic>);
  }

  /// 409 when the lot is not AT_RISK.
  Future<List<RescueMatch>> matches(String lotId) async {
    final response = await _dio.get<dynamic>(ApiConfig.rescueLotMatchesEndpoint(lotId));
    return (response.data as List<dynamic>)
        .map((e) => RescueMatch.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<RescueLot> markSold(String lotId) async {
    final response = await _dio.post<dynamic>(ApiConfig.rescueLotSoldEndpoint(lotId));
    return RescueLot.fromJson(response.data as Map<String, dynamic>);
  }

  /// Demo button: moves the lot's clock forward. The server answers 404 once it is switched off.
  Future<void> simulate({required double hours, required String lotId}) =>
      _dio.post<dynamic>(ApiConfig.rescueSimulateEndpoint, data: {'hours': hours, 'lot_id': lotId});

  Future<List<RescueAlert>> alerts({bool unreadOnly = false}) async {
    final response = await _dio.get<dynamic>(
      ApiConfig.rescueAlertsEndpoint,
      queryParameters: {if (unreadOnly) 'unread_only': true},
    );
    return (response.data as List<dynamic>)
        .map((e) => RescueAlert.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> markAlertRead(String alertId) =>
      _dio.post<dynamic>(ApiConfig.rescueAlertReadEndpoint(alertId));

  /// Latitude/longitude of the farmer's first farm that has a location, or null.
  /// Places a lot on the map (STATUS, Pre-flight defaults, item 3).
  Future<({double lat, double lng})?> farmLocation() async {
    final response = await _dio.get<dynamic>(ApiConfig.farmsEndpoint);
    final data = response.data;
    final items = data is Map<String, dynamic> ? (data['items'] as List<dynamic>? ?? const []) : const [];
    for (final item in items) {
      final farm = item as Map<String, dynamic>;
      final lat = double.tryParse('${farm['latitude']}');
      final lng = double.tryParse('${farm['longitude']}');
      if (lat != null && lng != null) return (lat: lat, lng: lng);
    }
    return null;
  }
}

/// A short message for the screen. Never shows the raw exception.
String rescueErrorMessage(Object error) {
  if (error is DioException) {
    final code = error.response?.statusCode;
    if (code == 401) return 'Please log in to continue.';
    if (code == 403) return 'Crop Rescue is for farmer accounts.';
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
