import 'package:dio/dio.dart';

import '../../models/listing_media_model.dart';
import '../config/api_config.dart';
import 'api_client.dart';

/// Lot photos/videos and admin verification. Who may do what is decided by the server from the login.
class ListingMediaApi {
  final Dio _dio = ApiClient().dio;

  Future<ListingMedia> list(String listingId) async {
    final response = await _dio.get<dynamic>(ApiConfig.listingMediaEndpoint(listingId));
    return ListingMedia.fromJson(response.data as Map<String, dynamic>);
  }

  /// Uploads one camera photo or video to the farmer's own lot.
  Future<ListingMedia> upload(
    String listingId, {
    required List<int> bytes,
    required String filename,
    required String contentType,
  }) async {
    final form = FormData.fromMap({
      'file': MultipartFile.fromBytes(bytes, filename: filename, contentType: DioMediaType.parse(contentType)),
    });
    final response = await _dio.post<dynamic>(
      ApiConfig.listingMediaEndpoint(listingId),
      data: form,
      // Videos can take a while on mobile data.
      options: Options(sendTimeout: const Duration(minutes: 2), receiveTimeout: const Duration(minutes: 2)),
    );
    return ListingMedia.fromJson(response.data as Map<String, dynamic>);
  }

  Future<ListingMedia> delete(String listingId, String mediaId) async {
    final response = await _dio.delete<dynamic>(ApiConfig.listingMediaItemEndpoint(listingId, mediaId));
    return ListingMedia.fromJson(response.data as Map<String, dynamic>);
  }

  /// Admin only: lots waiting for review (or `VERIFIED` / `REJECTED`).
  Future<List<VerificationQueueItem>> queue({String status = 'PENDING'}) async {
    final response = await _dio.get<dynamic>(
      ApiConfig.listingVerificationsEndpoint,
      queryParameters: {'status': status},
    );
    return (response.data as List<dynamic>)
        .map((e) => VerificationQueueItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Admin only: `VERIFIED`, or `REJECTED` with a reason the farmer will see.
  Future<ListingMedia> decide(String listingId, {required String decision, String? reason}) async {
    final response = await _dio.post<dynamic>(
      ApiConfig.listingVerificationEndpoint(listingId),
      data: {'decision': decision, if (reason != null && reason.trim().isNotEmpty) 'reason': reason.trim()},
    );
    return ListingMedia.fromJson(response.data as Map<String, dynamic>);
  }
}

/// Content type for a camera file, from its name. Null = not a photo/video the server accepts.
String? mediaContentType(String filename) {
  final name = filename.toLowerCase();
  if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'image/jpeg';
  if (name.endsWith('.png')) return 'image/png';
  if (name.endsWith('.webp')) return 'image/webp';
  if (name.endsWith('.mp4')) return 'video/mp4';
  if (name.endsWith('.mov')) return 'video/quicktime';
  return null;
}
