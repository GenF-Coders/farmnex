import 'package:dio/dio.dart';
import '../config/api_config.dart';
import '../storage/storage_service.dart';
import '../translation/translation_service.dart';

class ApiClient {
  late final Dio dio;
  StorageService? _storage;

  static final ApiClient _singleton = ApiClient._internal();
  factory ApiClient() => _singleton;

  ApiClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: ApiConfig.baseUrl,
        connectTimeout: const Duration(seconds: 20),
        receiveTimeout: const Duration(seconds: 20),
        sendTimeout: const Duration(seconds: 20),
        headers: const {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          _storage ??= await StorageService.getInstance();
          final token = _storage?.getAccessToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (DioException error, handler) async {
          final is401 = error.response?.statusCode == 401;
          final skipRefresh = error.requestOptions.extra['skipRefresh'] == true;
          final isRefreshCall =
              error.requestOptions.path == ApiConfig.refreshTokenEndpoint;

          if (is401 && !skipRefresh && !isRefreshCall) {
            final refreshed = await _refreshToken();
            if (refreshed) {
              try {
                final response = await _retryOriginalRequest(
                  error.requestOptions,
                );
                return handler.resolve(response);
              } on DioException catch (retryError) {
                return handler.next(retryError);
              }
            }
          }

          handler.next(error);
        },
      ),
    );
  }

  Future<bool> _refreshToken() async {
    try {
      _storage ??= await StorageService.getInstance();
      final refreshToken = _storage?.getRefreshToken();
      if (refreshToken == null || refreshToken.isEmpty) return false;

      final response = await dio.post(
        ApiConfig.refreshTokenEndpoint,
        data: {'refresh_token': refreshToken},
        options: Options(extra: {'skipRefresh': true}),
      );

      final data = _asMap(response.data);
      final accessToken = _readString(data, 'access_token');
      final newRefreshToken =
          _readString(data, 'refresh_token') ?? refreshToken;

      if (accessToken == null || accessToken.isEmpty) return false;

      await _storage?.saveTokens(
        accessToken: accessToken,
        refreshToken: newRefreshToken,
      );
      return true;
    } catch (_) {
      await _storage?.clearTokens();
      return false;
    }
  }

  Future<Response<dynamic>> _retryOriginalRequest(
    RequestOptions requestOptions,
  ) {
    final token = _storage?.getAccessToken();
    final headers = Map<String, dynamic>.from(requestOptions.headers);
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }

    return dio.request<dynamic>(
      requestOptions.path,
      data: requestOptions.data,
      queryParameters: requestOptions.queryParameters,
      options: Options(
        method: requestOptions.method,
        headers: headers,
        contentType: requestOptions.contentType,
        responseType: requestOptions.responseType,
        extra: {...requestOptions.extra, 'skipRefresh': true},
      ),
    );
  }

  Future<Response<dynamic>> get(
    String endpoint, {
    Map<String, dynamic>? queryParameters,
  }) {
    return dio.get(endpoint, queryParameters: queryParameters);
  }

  Future<Response<dynamic>> getTranslated(
    String endpoint, {
    Map<String, dynamic>? queryParameters,
    required String targetLanguage,
  }) async {
    final response = await get(endpoint, queryParameters: queryParameters);
    response.data = await TranslationService.translateContent(response.data, targetLanguage);
    return response;
  }

  Future<Response<dynamic>> postTranslated(
    String endpoint, {
    dynamic data,
    Options? options,
    required String targetLanguage,
  }) async {
    final response = await post(endpoint, data: data, options: options);
    response.data = await TranslationService.translateContent(response.data, targetLanguage);
    return response;
  }

  Future<Response<dynamic>> post(
    String endpoint, {
    dynamic data,
    Options? options,
  }) {
    return dio.post(endpoint, data: data, options: options);
  }

  Future<Response<dynamic>> patch(
    String endpoint, {
    dynamic data,
  }) {
    return dio.patch(endpoint, data: data);
  }

  Future<Response<dynamic>> delete(
    String endpoint, {
    dynamic data,
  }) {
    return dio.delete(endpoint, data: data);
  }

  Future<Response<dynamic>> download(
    String endpoint, {
    String? savePath,
  }) {
    return dio.get(
      endpoint,
      options: Options(responseType: ResponseType.bytes),
    );
  }

  static Map<String, dynamic> _asMap(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    return <String, dynamic>{};
  }

  static String? _readString(Map<String, dynamic> map, String key) {
    final value = map[key];
    return value is String && value.isNotEmpty ? value : null;
  }
}

String apiErrorMessage(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map) {
      final detail = data['detail'];
      if (detail is String && detail.isNotEmpty) return detail;
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map && first['msg'] is String) {
          return first['msg'] as String;
        }
      }
    }
    if (error.response?.statusCode != null) {
      return 'Request failed (${error.response!.statusCode}).';
    }
    return error.message ?? 'Network request failed.';
  }
  return error.toString();
}
