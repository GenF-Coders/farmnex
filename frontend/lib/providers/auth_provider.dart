import 'dart:convert';
import 'package:flutter/material.dart';
import '../core/config/api_config.dart';
import '../core/network/api_client.dart';
import '../core/network/backend_service.dart';
import '../core/storage/storage_service.dart';
import '../models/user_model.dart';

class AuthProvider extends ChangeNotifier {
  bool _isLoggedIn = false;
  UserModel? _user;
  PendingAction? _pendingAction;
  bool _isLoading = false;
  String? _errorMessage;
  StorageService? _storage;
  final BackendService _backend = BackendService();

  String? _registrationToken;
  String? _registrationPhone;
  String? _loginPhone;
  OtpRequestResponse? _lastOtpResponse;

  bool get isLoggedIn => _isLoggedIn;
  UserModel? get user => _user;
  PendingAction? get pendingAction => _pendingAction;
  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  OtpRequestResponse? get lastOtpResponse => _lastOtpResponse;
  bool get hasRegistrationProof =>
      _registrationToken != null && _registrationToken!.isNotEmpty;

  AuthProvider() {
    _initSession();
  }

  Future<void> _initSession() async {
    _storage = await StorageService.getInstance();
    final token = _storage?.getAccessToken();
    final userData = _storage?.getUserData();

    if (token != null && token.isNotEmpty && userData != null) {
      try {
        final jsonMap = jsonDecode(userData) as Map<String, dynamic>;
        _user = UserModel.fromJson(jsonMap);
        _isLoggedIn = _user != null && _user!.id.isNotEmpty;
        if (_isLoggedIn) {
          await refreshMyProfile();
        }
      } catch (_) {
        await _storage?.clearTokens();
        _isLoggedIn = false;
        _user = null;
      }
    }
    notifyListeners();
  }

  void setPendingAction(PendingAction? action) {
    _pendingAction = action;
    notifyListeners();
  }

  void clearPendingAction() {
    _pendingAction = null;
    notifyListeners();
  }

  Future<bool> requestRegistrationOtp({required String phone}) async {
    _beginLoading();
    try {
      final response = await ApiClient().post(
        ApiConfig.registerRequestOtpEndpoint,
        data: {'phone_number': _normalizePhone(phone)},
      );
      final result = OtpRequestResponse.fromJson(_map(response.data));
      _registrationPhone = _normalizePhone(phone);
      _lastOtpResponse = result;
      _errorMessage = null;
      _endLoading();
      return true;
    } catch (e) {
      _setError(apiErrorMessage(e));
      return false;
    }
  }

  Future<bool> resendRegistrationOtp() async {
    final phone = _registrationPhone;
    if (phone == null) {
      _setError('Enter your mobile number first.');
      return false;
    }
    _beginLoading();
    try {
      final response = await ApiClient().post(
        ApiConfig.registerResendOtpEndpoint,
        data: {'phone_number': phone},
      );
      _lastOtpResponse = OtpRequestResponse.fromJson(_map(response.data));
      _errorMessage = null;
      _endLoading();
      return true;
    } catch (e) {
      _setError(apiErrorMessage(e));
      return false;
    }
  }

  Future<bool> verifyRegistrationOtp({required String otp}) async {
    final phone = _registrationPhone;
    if (phone == null) {
      _setError('Request an OTP first.');
      return false;
    }
    _beginLoading();
    try {
      final response = await ApiClient().post(
        ApiConfig.registerVerifyOtpEndpoint,
        data: {
          'phone_number': phone,
          'otp': otp.trim(),
        },
      );
      final result = RegistrationVerificationResponse.fromJson(
        _map(response.data),
      );
      _registrationToken = result.registrationToken;
      _errorMessage = null;
      _endLoading();
      return true;
    } catch (e) {
      _setError(apiErrorMessage(e));
      return false;
    }
  }

  Future<bool> completeRegistration({required UserRole role}) async {
    final token = _registrationToken;
    if (token == null || token.isEmpty) {
      _setError('Verify the OTP before completing registration.');
      return false;
    }
    _beginLoading();
    try {
      final response = await ApiClient().post(
        ApiConfig.registerCompleteEndpoint,
        data: {
          'registration_token': token,
          'role': role.apiValue,
        },
      );
      final result = AuthTokenResponse.fromJson(_map(response.data));
      await _saveAuthenticatedSession(result);
      await refreshMyProfile();
      _registrationToken = null;
      _registrationPhone = null;
      _lastOtpResponse = null;
      _errorMessage = null;
      _endLoading();
      return true;
    } catch (e) {
      _setError(apiErrorMessage(e));
      return false;
    }
  }

  Future<bool> requestLoginOtp({required String phone}) async {
    _beginLoading();
    try {
      final normalized = _normalizePhone(phone);
      final response = await ApiClient().post(
        ApiConfig.loginRequestOtpEndpoint,
        data: {'phone_number': normalized},
      );
      _lastOtpResponse = OtpRequestResponse.fromJson(_map(response.data));
      _loginPhone = normalized;
      _errorMessage = null;
      _endLoading();
      return true;
    } catch (e) {
      _setError(apiErrorMessage(e));
      return false;
    }
  }

  Future<bool> resendLoginOtp() async {
    final phone = _loginPhone;
    if (phone == null) {
      _setError('Enter your mobile number first.');
      return false;
    }
    _beginLoading();
    try {
      final response = await ApiClient().post(
        ApiConfig.loginResendOtpEndpoint,
        data: {'phone_number': phone},
      );
      _lastOtpResponse = OtpRequestResponse.fromJson(_map(response.data));
      _errorMessage = null;
      _endLoading();
      return true;
    } catch (e) {
      _setError(apiErrorMessage(e));
      return false;
    }
  }

  Future<bool> verifyLoginOtp({required String otp}) async {
    final phone = _loginPhone;
    if (phone == null) {
      _setError('Request a login OTP first.');
      return false;
    }
    _beginLoading();
    try {
      final response = await ApiClient().post(
        ApiConfig.loginVerifyOtpEndpoint,
        data: {
          'phone_number': phone,
          'otp': otp.trim(),
        },
      );
      final result = AuthTokenResponse.fromJson(_map(response.data));
      await _saveAuthenticatedSession(result);
      await refreshMyProfile();
      _loginPhone = null;
      _lastOtpResponse = null;
      _errorMessage = null;
      _endLoading();
      return true;
    } catch (e) {
      _setError(apiErrorMessage(e));
      return false;
    }
  }

  Future<bool> refreshMyProfile() async {
    if (!_isLoggedIn && _user == null) return false;
    try {
      final response = await _backend.getMyProfile();
      final raw = response.data;
      if (raw is! Map) return false;
      final data = Map<String, dynamic>.from(raw);

      final profileRaw = data['profile'];
      final profile = profileRaw is Map
          ? Map<String, dynamic>.from(profileRaw)
          : data;

      final current = _user;
      if (current == null) return false;

      final profileRole = UserRole.fromString(
        profile['role']?.toString() ?? profile['user_role']?.toString(),
      );
      final merged = current.copyWith(
        id: (profile['public_id'] ?? profile['id'] ?? current.id).toString(),
        role: profileRole == UserRole.guest ? current.role : profileRole,
        name: (profile['full_name'] ??
                profile['name'] ??
                profile['display_name'] ??
                current.name)
            .toString(),
        mobile: (profile['phone_number'] ??
                profile['mobile'] ??
                current.mobile)
            .toString(),
        address: (profile['address'] ?? current.address).toString(),
        companyName: profile['company_name']?.toString() ?? current.companyName,
        gstin: profile['gstin']?.toString() ?? current.gstin,
      );

      _user = merged;
      await _storage?.saveUserData(jsonEncode(merged.toJson()));
      notifyListeners();
      return true;
    } catch (_) {

      return false;
    }
  }

  Future<bool> updateMyProfile({
    String? name,
    String? address,
    String? companyName,
    String? gstin,
    String? dateOfBirth,
    String? gender,
    String? surname,
  }) async {
    if (!_isLoggedIn) return false;
    try {
      final body = <String, dynamic>{};
      if (name != null && name.isNotEmpty) body['full_name'] = name;
      if (address != null && address.isNotEmpty) body['address'] = address;
      if (companyName != null && companyName.isNotEmpty) body['company_name'] = companyName;
      if (gstin != null && gstin.isNotEmpty) body['gstin'] = gstin;
      if (dateOfBirth != null && dateOfBirth.isNotEmpty) body['date_of_birth'] = dateOfBirth;
      if (gender != null && gender.isNotEmpty) body['gender'] = gender;
      if (surname != null && surname.isNotEmpty) body['surname'] = surname;
      if (body.isEmpty) return true;
      final response = await _backend.updateMyProfile(body);
      final raw = response.data;
      if (raw is Map) {
        final map = Map<String, dynamic>.from(raw);
        final profileRaw = map['profile'];
        final profile = profileRaw is Map ? Map<String, dynamic>.from(profileRaw) : map;
        final current = _user;
        if (current != null) {
          _user = current.copyWith(
            name: (profile['full_name'] ?? current.name).toString(),
            address: (profile['address'] ?? current.address).toString(),
            companyName: profile['company_name']?.toString() ?? current.companyName,
            gstin: profile['gstin']?.toString() ?? current.gstin,
          );
          await _storage?.saveUserData(jsonEncode(_user!.toJson()));
          notifyListeners();
        }
      }
      return true;
    } catch (e) {
      _errorMessage = apiErrorMessage(e);
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    _storage ??= await StorageService.getInstance();
    final refreshToken = _storage?.getRefreshToken();

    try {
      if (refreshToken != null && refreshToken.isNotEmpty) {
        await ApiClient().post(
          ApiConfig.logoutEndpoint,
          data: {'refresh_token': refreshToken},
        );
      }
    } catch (_) {

    }

    await _storage?.clearTokens();
    _isLoggedIn = false;
    _user = null;
    _pendingAction = null;
    _registrationToken = null;
    _registrationPhone = null;
    _loginPhone = null;
    _lastOtpResponse = null;
    _errorMessage = null;
    notifyListeners();
  }

  Future<void> _saveAuthenticatedSession(AuthTokenResponse result) async {
    _storage ??= await StorageService.getInstance();
    await _storage?.saveTokens(
      accessToken: result.accessToken,
      refreshToken: result.refreshToken,
    );

    if (result.user != null) {
      final backendRole = result.role ?? result.user!.role;
      _user = result.user!.copyWith(role: backendRole);
    } else if (result.role != null) {
      _user = UserModel(
        id: '',
        name: 'User',
        mobile: _loginPhone ?? _registrationPhone ?? '',
        role: result.role!,
        address: '',
      );
    } else {
      _user = UserModel(
        id: '',
        name: 'User',
        mobile: _loginPhone ?? _registrationPhone ?? '',
        role: UserRole.guest,
        address: '',
      );
    }

    await _storage?.saveUserData(jsonEncode(_user!.toJson()));
    _isLoggedIn = true;
    notifyListeners();
  }

  static String _normalizePhone(String phone) =>
      phone.replaceAll(RegExp(r'\D'), '');

  static Map<String, dynamic> _map(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    throw const FormatException('Invalid JSON response from FastAPI.');
  }

  void _beginLoading() {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
  }

  void _endLoading() {
    _isLoading = false;
    notifyListeners();
  }

  void _setError(String message) {
    _isLoading = false;
    _errorMessage = message;
    notifyListeners();
  }
}
