import 'package:dio/dio.dart';

import '../../models/waste_model.dart';
import '../config/api_config.dart';
import 'api_client.dart';
import 'listing_api.dart' show listingErrorMessage;

/// Waste for sale. A listing needs a waste record first (S13 rule); identity comes from the login token.
class WasteApi {
  final Dio _dio = ApiClient().dio;

  /// Every active lot, or only the signed-in farmer's own lots in any status (`mine`).
  Future<List<WasteItem>> list({bool mine = false}) async {
    final response = await _dio.get<dynamic>(
      ApiConfig.wasteListingsEndpoint,
      queryParameters: {'limit': 100, if (mine) 'mine': true},
    );
    final data = response.data as List<dynamic>;
    return data.map((e) => WasteItem.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Records the waste on a farm, then lists it for sale. Returns the new listing.
  Future<WasteItem> create({
    required String farmId,
    required String wasteType,
    required String utilizationType,
    required double quantity,
    required String unit,
    required double pricePerUnit,
  }) async {
    final record = await _dio.post<dynamic>(ApiConfig.wasteRecordsEndpoint, data: {
      'farm_id': farmId,
      'waste_type': wasteType,
      'quantity': quantity.toString(),
      'unit': unit,
    });
    final recordId = (record.data as Map<String, dynamic>)['public_id'].toString();
    final response = await _dio.post<dynamic>(ApiConfig.wasteListingsEndpoint, data: {
      'waste_record_id': recordId,
      'title': wasteType,
      'utilization_type': utilizationType,
      'quantity': quantity.toString(),
      'unit': unit,
      'price': pricePerUnit.toString(),
    });
    return WasteItem.fromJson(response.data as Map<String, dynamic>);
  }
}

/// A short message for the screen (same wording as the listing screens).
String wasteErrorMessage(Object error) => listingErrorMessage(error);
