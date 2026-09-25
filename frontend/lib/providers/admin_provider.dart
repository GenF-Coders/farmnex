import 'package:flutter/material.dart';

import '../models/user_model.dart';

class KycRequest {
  final String id;
  final String applicantName;
  final UserRole role;
  final String documentType;
  final String documentNumber;
  final String submittedAgo;
  final String status;

  const KycRequest({
    required this.id,
    required this.applicantName,
    required this.role,
    required this.documentType,
    required this.documentNumber,
    required this.submittedAgo,
    this.status = 'pending',
  });

  String get roleSymbol {
    switch (role) {
      case UserRole.farmer:
        return '🧑‍🌾';
      case UserRole.buyer:
        return '🏢';
      case UserRole.logistics:
        return '🚚';
      case UserRole.admin:
        return '🛡️';
      case UserRole.guest:
        return '👤';
    }
  }

  KycRequest copyWith({String? status}) => KycRequest(
        id: id,
        applicantName: applicantName,
        role: role,
        documentType: documentType,
        documentNumber: documentNumber,
        submittedAgo: submittedAgo,
        status: status ?? this.status,
      );
}

class PlatformUser {
  final String id;
  final String name;
  final UserRole role;
  final String location;
  final bool isVerified;
  final bool isSuspended;
  final int trades;

  const PlatformUser({
    required this.id,
    required this.name,
    required this.role,
    required this.location,
    required this.trades,
    this.isVerified = true,
    this.isSuspended = false,
  });

  String get roleSymbol {
    switch (role) {
      case UserRole.farmer:
        return '🧑‍🌾';
      case UserRole.buyer:
        return '🏢';
      case UserRole.logistics:
        return '🚚';
      case UserRole.admin:
        return '🛡️';
      case UserRole.guest:
        return '👤';
    }
  }

  PlatformUser copyWith({bool? isSuspended}) => PlatformUser(
        id: id,
        name: name,
        role: role,
        location: location,
        trades: trades,
        isVerified: isVerified,
        isSuspended: isSuspended ?? this.isSuspended,
      );
}

class SettlementRow {
  final String id;
  final String symbol;
  final String party;
  final double amount;
  final String status;
  final String ago;

  const SettlementRow({
    required this.id,
    required this.symbol,
    required this.party,
    required this.amount,
    required this.status,
    required this.ago,
  });
}

class AdminProvider extends ChangeNotifier {
  final List<KycRequest> _kycQueue = [
    const KycRequest(
      id: 'kyc-1',
      applicantName: 'Sunil Bhosale',
      role: UserRole.farmer,
      documentType: '📜 7/12 Land Extract',
      documentNumber: 'MH-LAT-7712-0091',
      submittedAgo: '12 min',
    ),
    const KycRequest(
      id: 'kyc-2',
      applicantName: 'AgroCorp India Traders',
      role: UserRole.buyer,
      documentType: '🧾 GSTIN Certificate',
      documentNumber: '27AAFCA1234K1ZP',
      submittedAgo: '48 min',
    ),
    const KycRequest(
      id: 'kyc-3',
      applicantName: 'Imran Shaikh',
      role: UserRole.logistics,
      documentType: '🚛 Vehicle RC + Permit',
      documentNumber: 'MH-12-KL-4478',
      submittedAgo: '2 hr',
    ),
    const KycRequest(
      id: 'kyc-4',
      applicantName: 'Lakshmi Reddy',
      role: UserRole.farmer,
      documentType: '📜 Pattadar Passbook',
      documentNumber: 'TS-KRM-3391-0042',
      submittedAgo: '5 hr',
    ),
  ];

  final List<PlatformUser> _users = [
    const PlatformUser(id: 'u1', name: 'Ramesh Patil', role: UserRole.farmer, location: 'Indore, MP', trades: 42),
    const PlatformUser(id: 'u2', name: 'Vikram Sethi', role: UserRole.buyer, location: 'Lasalgaon, MH', trades: 128),
    const PlatformUser(id: 'u3', name: 'Imran Shaikh', role: UserRole.logistics, location: 'Pune, MH', trades: 67, isVerified: false),
    const PlatformUser(id: 'u4', name: 'Balasaheb Shinde', role: UserRole.farmer, location: 'Latur, MH', trades: 19),
    const PlatformUser(id: 'u5', name: 'Adani Wilmar Ltd', role: UserRole.buyer, location: 'Pune, MH', trades: 311),
    const PlatformUser(id: 'u6', name: 'Deepak Yadav', role: UserRole.logistics, location: 'Nashik, MH', trades: 8, isSuspended: true),
  ];

  final List<SettlementRow> settlements = const [
    SettlementRow(id: 's1', symbol: '🔒', party: 'Kishanlal Agro ➜ Ramesh Patil', amount: 252000, status: 'escrow', ago: '15 min'),
    SettlementRow(id: 's2', symbol: '✅', party: 'Adani Wilmar ➜ B. Shinde', amount: 246000, status: 'settled', ago: '3 hr'),
    SettlementRow(id: 's3', symbol: '🚚', party: 'Freight payout ➜ I. Shaikh', amount: 11200, status: 'settled', ago: '5 hr'),
    SettlementRow(id: 's4', symbol: '↩️', party: 'Refund ➜ AgroCorp India', amount: 38400, status: 'refunded', ago: '1 day'),
  ];

  List<KycRequest> get kycQueue => List.unmodifiable(_kycQueue);

  List<KycRequest> get pendingKyc =>
      _kycQueue.where((k) => k.status == 'pending').toList();

  List<PlatformUser> get users => List.unmodifiable(_users);

  int get pendingKycCount => pendingKyc.length;

  int get farmerCount => _users.where((u) => u.role == UserRole.farmer).length;
  int get buyerCount => _users.where((u) => u.role == UserRole.buyer).length;
  int get logisticsCount => _users.where((u) => u.role == UserRole.logistics).length;
  int get suspendedCount => _users.where((u) => u.isSuspended).length;

  double get escrowLocked => settlements
      .where((s) => s.status == 'escrow')
      .fold<double>(0, (sum, s) => sum + s.amount);

  double get settledToday => settlements
      .where((s) => s.status == 'settled')
      .fold<double>(0, (sum, s) => sum + s.amount);

  void approveKyc(String id) => _decide(id, 'approved');

  void rejectKyc(String id) => _decide(id, 'rejected');

  void toggleSuspend(String userId) {
    final index = _users.indexWhere((u) => u.id == userId);
    if (index == -1) return;
    _users[index] = _users[index].copyWith(isSuspended: !_users[index].isSuspended);
    notifyListeners();
  }

  void _decide(String id, String status) {
    final index = _kycQueue.indexWhere((k) => k.id == id);
    if (index == -1) return;
    _kycQueue[index] = _kycQueue[index].copyWith(status: status);
    notifyListeners();
  }
}
