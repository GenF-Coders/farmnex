enum UserRole {
  farmer,
  buyer,
  logistics,
  admin,
  guest;

  String get displayName {
    switch (this) {
      case UserRole.farmer:
        return 'Farmer';
      case UserRole.buyer:
        return 'Buyer';
      case UserRole.logistics:
        return 'Logistics';
      case UserRole.admin:
        return 'Admin';
      case UserRole.guest:
        return 'Guest';
    }
  }

  String get apiValue {
    switch (this) {
      case UserRole.farmer:
        return 'FARMER';
      case UserRole.buyer:
        return 'BUYER';
      case UserRole.logistics:
        return 'LOGISTIC';
      case UserRole.admin:
        return 'ADMIN';
      case UserRole.guest:
        return 'GUEST';
    }
  }

  static UserRole fromString(String? role) {
    switch ((role ?? '').toLowerCase().replaceAll('-', '').replaceAll('_', '')) {
      case 'farmer':
        return UserRole.farmer;
      case 'buyer':
      case 'customer':
        return UserRole.buyer;
      case 'logistic':
      case 'logistics':
      case 'logisticpartner':
      case 'transporter':
      case 'transport':
        return UserRole.logistics;
      case 'admin':
      case 'superadmin':
        return UserRole.admin;
      default:
        return UserRole.guest;
    }
  }
}

class PendingAction {
  final String type;
  final String? cropId;
  final String? cropName;

  const PendingAction({
    required this.type,
    this.cropId,
    this.cropName,
  });

  Map<String, dynamic> toJson() => {
        'type': type,
        'cropId': cropId,
        'cropName': cropName,
      };

  factory PendingAction.fromJson(Map<String, dynamic> json) => PendingAction(
        type: json['type'] as String,
        cropId: json['cropId'] as String?,
        cropName: json['cropName'] as String?,
      );
}

class UserModel {

  final String id;
  final String name;
  final String mobile;
  final UserRole role;
  final String address;
  final bool isVerified;
  final String verificationStatus;
  final String? companyName;
  final String? gstin;

  const UserModel({
    required this.id,
    required this.name,
    required this.mobile,
    required this.role,
    required this.address,
    this.isVerified = false,
    this.verificationStatus = 'none',
    this.companyName,
    this.gstin,
  });

  UserModel copyWith({
    String? id,
    String? name,
    String? mobile,
    UserRole? role,
    String? address,
    bool? isVerified,
    String? verificationStatus,
    String? companyName,
    String? gstin,
  }) {
    return UserModel(
      id: id ?? this.id,
      name: name ?? this.name,
      mobile: mobile ?? this.mobile,
      role: role ?? this.role,
      address: address ?? this.address,
      isVerified: isVerified ?? this.isVerified,
      verificationStatus: verificationStatus ?? this.verificationStatus,
      companyName: companyName ?? this.companyName,
      gstin: gstin ?? this.gstin,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'mobile': mobile,
        'role': role.name,
        'address': address,
        'isVerified': isVerified,
        'verificationStatus': verificationStatus,
        'companyName': companyName,
        'gstin': gstin,
      };

  factory UserModel.fromJson(Map<String, dynamic> json) {
    final id = (json['id'] ?? json['public_id'] ?? '').toString();
    final mobile = (json['mobile'] ?? json['phone_number'] ?? '').toString();
    final name = (json['name'] ?? json['full_name'] ?? mobile).toString();
    final verified = json['isVerified'] ?? json['phone_verified'] ?? false;
    final status =
        (json['verificationStatus'] ?? json['account_status'] ?? 'none')
            .toString();

    return UserModel(
      id: id,
      name: name.isEmpty ? 'User' : name,
      mobile: mobile,
      role: UserRole.fromString(json['role']?.toString()),
      address: (json['address'] ?? '').toString(),
      isVerified: verified is bool ? verified : false,
      verificationStatus: status,
      companyName: json['companyName']?.toString(),
      gstin: json['gstin']?.toString(),
    );
  }

  factory UserModel.fromAuthUserJson(Map<String, dynamic> json) {
    return UserModel(
      id: (json['public_id'] ?? json['id'] ?? '').toString(),
      name: (json['name'] ?? json['full_name'] ?? json['phone_number'] ?? 'User')
          .toString(),
      mobile: (json['phone_number'] ?? json['mobile'] ?? '').toString(),
      role: UserRole.fromString(json['role']?.toString()),
      address: (json['address'] ?? '').toString(),
      isVerified: json['phone_verified'] == true || json['isVerified'] == true,
      verificationStatus:
          (json['account_status'] ?? json['verificationStatus'] ?? 'none')
              .toString(),
      companyName: json['company_name']?.toString() ?? json['companyName']?.toString(),
      gstin: json['gstin']?.toString(),
    );
  }
}

class AuthTokenResponse {
  final String accessToken;
  final String refreshToken;
  final int expiresIn;
  final UserModel? user;
  final UserRole? role;

  const AuthTokenResponse({
    required this.accessToken,
    required this.refreshToken,
    required this.expiresIn,
    this.user,
    this.role,
  });

  factory AuthTokenResponse.fromJson(Map<String, dynamic> json) {
    final access = json['access_token'];
    final refresh = json['refresh_token'];
    if (access is! String || refresh is! String) {
      throw const FormatException('FastAPI response did not contain access_token and refresh_token.');
    }

    final rawUser = json['user'];
    final topLevelRole = UserRole.fromString(
      json['role']?.toString() ?? json['user_role']?.toString(),
    );
    final parsedUser = rawUser is Map
        ? UserModel.fromAuthUserJson(Map<String, dynamic>.from(rawUser))
        : null;
    final resolvedRole = parsedUser != null && parsedUser.role != UserRole.guest
        ? parsedUser.role
        : (topLevelRole == UserRole.guest ? null : topLevelRole);
    return AuthTokenResponse(
      accessToken: access,
      refreshToken: refresh,
      expiresIn: _safeInt(json['expires_in']),
      user: parsedUser,
      role: resolvedRole,
    );
  }
}

class OtpRequestResponse {
  final String otpId;
  final int expiresInSeconds;
  final int resendAvailableInSeconds;

  const OtpRequestResponse({
    required this.otpId,
    required this.expiresInSeconds,
    required this.resendAvailableInSeconds,
  });

  factory OtpRequestResponse.fromJson(Map<String, dynamic> json) {
    final otpId = json['otp_id'];
    if (otpId is! String || otpId.isEmpty) {
      throw const FormatException('FastAPI response did not contain otp_id.');
    }
    return OtpRequestResponse(
      otpId: otpId,
      expiresInSeconds: _safeInt(json['expires_in_seconds']),
      resendAvailableInSeconds: _safeInt(json['resend_available_in_seconds']),
    );
  }
}

class RegistrationVerificationResponse {
  final String registrationToken;

  const RegistrationVerificationResponse({required this.registrationToken});

  factory RegistrationVerificationResponse.fromJson(Map<String, dynamic> json) {
    final token = json['registration_token'] ??
        json['registrationToken'] ??
        json['token'];
    if (token is! String || token.isEmpty) {
      throw const FormatException(
        'FastAPI verification response did not contain a registration token.',
      );
    }
    return RegistrationVerificationResponse(registrationToken: token);
  }
}

int _safeInt(dynamic value) {
  if (value is int) return value;
  if (value is num) return value.toInt();
  if (value is String) return int.tryParse(value) ?? 0;
  return 0;
}
