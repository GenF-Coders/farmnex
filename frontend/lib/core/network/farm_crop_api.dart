import 'package:dio/dio.dart';

import '../../models/listing_model.dart';
import '../config/api_config.dart';
import 'api_client.dart';
import 'backend_service.dart';

/// The setup a farmer needs before a listing: farm → farm crop → crop batch (S12 rule).
class FarmCropApi {
  final Dio _dio = ApiClient().dio;
  final BackendService _backend = BackendService();

  Future<List<CropTypeModel>> listCropTypes() async {
    final response = await _dio.get<dynamic>(ApiConfig.cropTypesEndpoint, queryParameters: {'limit': 100});
    final data = response.data as List<dynamic>;
    return data.map((e) => CropTypeModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// The farmer's own farms (existing `BackendService.listFarms`).
  Future<List<FarmSummary>> listMyFarms() async {
    final response = await _backend.listFarms();
    final items = (response.data as Map<String, dynamic>)['items'] as List<dynamic>;
    return items.map((e) => FarmSummary.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Existing `BackendService.createFarm`.
  Future<FarmSummary> createFarm({
    required String farmName,
    required String addressLine1,
    required String city,
    required String district,
    required String state,
    required String postalCode,
  }) async {
    final response = await _backend.createFarm({
      'farm_name': farmName,
      'address_line_1': addressLine1,
      'city': city,
      'district': district,
      'state': state,
      'postal_code': postalCode,
    });
    return FarmSummary.fromJson(response.data as Map<String, dynamic>);
  }

  /// Creates the farm crop and its batch; returns the batch's public id.
  Future<String> createFarmCropAndBatch({
    required String farmId,
    required String cropTypeId,
    required double quantity,
    required String unit,
    String? qualityGrade,
    bool organic = false,
  }) async {
    final crop = await _dio.post<dynamic>(ApiConfig.farmCropsEndpoint, data: {
      'farm_id': farmId,
      'crop_type_id': cropTypeId,
    });
    final farmCropId = (crop.data as Map<String, dynamic>)['public_id'].toString();
    final batch = await _dio.post<dynamic>(ApiConfig.cropBatchesEndpoint, data: {
      'farm_crop_id': farmCropId,
      'quantity': quantity.toString(),
      'unit': unit,
      'quality_grade': ?qualityGrade,
      'organic_certified': organic,
    });
    return (batch.data as Map<String, dynamic>)['public_id'].toString();
  }
}
