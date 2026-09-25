import 'package:dio/dio.dart';
import '../config/api_config.dart';
import 'api_client.dart';

class BackendService {
  final ApiClient _client = ApiClient();

  Future<Response<dynamic>> health() => _client.get(ApiConfig.healthEndpoint);
  Future<Response<dynamic>> databaseHealth() => _client.get(ApiConfig.databaseHealthEndpoint);
  Future<Response<dynamic>> readiness() => _client.get(ApiConfig.readinessEndpoint);

  Future<Response<dynamic>> requestRegistrationOtp(String phone) =>
      _client.post(ApiConfig.registerRequestOtpEndpoint, data: {'phone_number': phone});
  Future<Response<dynamic>> resendRegistrationOtp(String phone) =>
      _client.post(ApiConfig.registerResendOtpEndpoint, data: {'phone_number': phone});
  Future<Response<dynamic>> verifyRegistrationOtp(String phone, String otp) =>
      _client.post(ApiConfig.registerVerifyOtpEndpoint, data: {'phone_number': phone, 'otp': otp});
  Future<Response<dynamic>> completeRegistration(Map<String, dynamic> body) =>
      _client.post(ApiConfig.registerCompleteEndpoint, data: body);

  Future<Response<dynamic>> requestLoginOtp(String phone) =>
      _client.post(ApiConfig.loginRequestOtpEndpoint, data: {'phone_number': phone});
  Future<Response<dynamic>> resendLoginOtp(String phone) =>
      _client.post(ApiConfig.loginResendOtpEndpoint, data: {'phone_number': phone});
  Future<Response<dynamic>> verifyLoginOtp(String phone, String otp) =>
      _client.post(ApiConfig.loginVerifyOtpEndpoint, data: {'phone_number': phone, 'otp': otp});
  Future<Response<dynamic>> refreshToken(String refreshToken) =>
      _client.post(ApiConfig.refreshTokenEndpoint,
          data: {'refresh_token': refreshToken},
          options: Options(extra: {'skipRefresh': true}));
  Future<Response<dynamic>> logout(String refreshToken) =>
      _client.post(ApiConfig.logoutEndpoint,
          data: {'refresh_token': refreshToken},
          options: Options(extra: {'skipRefresh': true}));

  Future<Response<dynamic>> getMyProfile() => _client.get(ApiConfig.myProfileEndpoint);
  Future<Response<dynamic>> updateMyProfile(Map<String, dynamic> body) =>
      _client.patch(ApiConfig.myProfileEndpoint, data: body);
  Future<Response<dynamic>> getMyProfileImageUrl() => _client.get(ApiConfig.myProfileImageEndpoint);
  Future<Response<dynamic>> uploadProfileImage(FormData data) =>
      _client.post(ApiConfig.myProfileImageEndpoint,
          data: data, options: Options(contentType: 'multipart/form-data'));
  Future<Response<dynamic>> deleteProfileImage() => _client.delete(ApiConfig.myProfileImageEndpoint);
  Future<Response<dynamic>> listUsers({Map<String, dynamic>? queryParameters}) =>
      _client.get(ApiConfig.usersEndpoint, queryParameters: queryParameters);
  Future<Response<dynamic>> getUser(String publicId) => _client.get(ApiConfig.userEndpoint(publicId));

  Future<Response<dynamic>> listMyAddresses() => _client.get(ApiConfig.addressesEndpoint);
  Future<Response<dynamic>> createMyAddress(Map<String, dynamic> body) =>
      _client.post(ApiConfig.addressesEndpoint, data: body);
  Future<Response<dynamic>> getMyAddress(String id) => _client.get(ApiConfig.addressEndpoint(id));
  Future<Response<dynamic>> updateMyAddress(String id, Map<String, dynamic> body) =>
      _client.patch(ApiConfig.addressEndpoint(id), data: body);
  Future<Response<dynamic>> deleteMyAddress(String id) => _client.delete(ApiConfig.addressEndpoint(id));
  Future<Response<dynamic>> setDefaultAddress(String id) => _client.post(ApiConfig.defaultAddressEndpoint(id));
  Future<Response<dynamic>> clearDefaultAddress(String id) => _client.delete(ApiConfig.defaultAddressEndpoint(id));
  Future<Response<dynamic>> deactivateAddress(String id) => _client.post(ApiConfig.deactivateAddressEndpoint(id));
  Future<Response<dynamic>> activateAddress(String id) => _client.post(ApiConfig.activateAddressEndpoint(id));

  Future<Response<dynamic>> createFarm(Map<String, dynamic> body) =>
      _client.post(ApiConfig.farmsEndpoint, data: body);
  Future<Response<dynamic>> listFarms() => _client.get(ApiConfig.farmsEndpoint);
  Future<Response<dynamic>> getFarm(String id) => _client.get(ApiConfig.farmEndpoint(id));
  Future<Response<dynamic>> updateFarm(String id, Map<String, dynamic> body) =>
      _client.patch(ApiConfig.farmEndpoint(id), data: body);
  Future<Response<dynamic>> deleteFarm(String id) => _client.delete(ApiConfig.farmEndpoint(id));
  Future<Response<dynamic>> uploadFarmFile(String id, FormData data) =>
      _client.post(ApiConfig.farmFileEndpoint(id),
          data: data, options: Options(contentType: 'multipart/form-data'));
  Future<Response<dynamic>> getFarmFileUrl(String id) => _client.get(ApiConfig.farmFileEndpoint(id));
  Future<Response<dynamic>> deleteFarmFile(String id) => _client.delete(ApiConfig.farmFileEndpoint(id));
  Future<Response<dynamic>> downloadFarmFile(String id) => _client.get(ApiConfig.farmFileDownloadEndpoint(id));
}
