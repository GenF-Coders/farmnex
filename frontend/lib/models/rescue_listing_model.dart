// Crop Rescue data, exactly as `/api/v2/rescue/...` returns it (snake_case keys).
// A "lot" is a harvested batch the farmer is watching for spoilage.

double _num(dynamic v) => v is num ? v.toDouble() : double.tryParse('$v') ?? 0;

DateTime? _time(dynamic v) => v == null ? null : DateTime.tryParse(v.toString())?.toLocal();

/// One of the crops Crop Rescue knows a shelf life for (`GET /rescue/crops`).
class RescueCrop {
  final String code;
  final String nameEn;
  final String nameMr;
  final double lifeHoursAt25c;

  const RescueCrop({
    required this.code,
    required this.nameEn,
    required this.nameMr,
    required this.lifeHoursAt25c,
  });

  factory RescueCrop.fromJson(Map<String, dynamic> json) => RescueCrop(
        code: json['code']?.toString() ?? '',
        nameEn: json['name_en']?.toString() ?? '',
        nameMr: json['name_mr']?.toString() ?? '',
        lifeHoursAt25c: _num(json['life_hours_at_25c']),
      );
}

class RescueCheck {
  final DateTime? checkedAt;
  final double temperatureC;
  final double remainingHours;
  final String status;

  const RescueCheck({
    required this.checkedAt,
    required this.temperatureC,
    required this.remainingHours,
    required this.status,
  });

  factory RescueCheck.fromJson(Map<String, dynamic> json) => RescueCheck(
        checkedAt: _time(json['checked_at']),
        temperatureC: _num(json['temperature_c']),
        remainingHours: _num(json['remaining_hours']),
        status: json['status']?.toString() ?? '',
      );
}

class RescueLot {
  final String id;
  final String cropCode;
  final double quantityKg;
  final DateTime? harvestedAt;
  final String storageMode;
  final double floorPricePerKg;
  final double? remainingHours;
  final DateTime? spoilEta;

  /// `FRESH`, `AT_RISK`, `SPOILED` or `SOLD`.
  final String status;
  final List<RescueCheck> checks;

  const RescueLot({
    required this.id,
    required this.cropCode,
    required this.quantityKg,
    required this.harvestedAt,
    required this.storageMode,
    required this.floorPricePerKg,
    required this.remainingHours,
    required this.spoilEta,
    required this.status,
    this.checks = const [],
  });

  bool get isOpen => status == 'FRESH' || status == 'AT_RISK';
  bool get isAtRisk => status == 'AT_RISK';

  factory RescueLot.fromJson(Map<String, dynamic> json) => RescueLot(
        id: json['id']?.toString() ?? '',
        cropCode: json['crop_code']?.toString() ?? '',
        quantityKg: _num(json['quantity_kg']),
        harvestedAt: _time(json['harvested_at']),
        storageMode: json['storage_mode']?.toString() ?? 'ambient',
        floorPricePerKg: _num(json['floor_price_per_kg']),
        remainingHours: json['remaining_hours'] == null ? null : _num(json['remaining_hours']),
        spoilEta: _time(json['spoil_eta']),
        status: json['status']?.toString() ?? 'FRESH',
        checks: ((json['checks'] as List<dynamic>?) ?? const [])
            .map((e) => RescueCheck.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

/// A nearby buyer ranked for an at-risk lot (`GET /rescue/lots/{id}/matches`).
class RescueMatch {
  final String buyerName;
  final double netPricePerKg;
  final double distanceKm;
  final double travelHours;
  final double qtyKg;
  final String reason;

  const RescueMatch({
    required this.buyerName,
    required this.netPricePerKg,
    required this.distanceKm,
    required this.travelHours,
    required this.qtyKg,
    required this.reason,
  });

  factory RescueMatch.fromJson(Map<String, dynamic> json) => RescueMatch(
        buyerName: json['buyer_name']?.toString() ?? '',
        netPricePerKg: _num(json['net_price_per_kg']),
        distanceKm: _num(json['distance_km']),
        travelHours: _num(json['travel_hours']),
        qtyKg: _num(json['qty_kg']),
        reason: json['reason']?.toString() ?? '',
      );
}

class RescueAlert {
  final String id;
  final String lotId;

  /// `AT_RISK` or `SPOILED`.
  final String kind;
  final String title;
  final String body;
  final DateTime? createdAt;
  final bool read;

  const RescueAlert({
    required this.id,
    required this.lotId,
    required this.kind,
    required this.title,
    required this.body,
    required this.createdAt,
    required this.read,
  });

  factory RescueAlert.fromJson(Map<String, dynamic> json) => RescueAlert(
        id: json['id']?.toString() ?? '',
        lotId: json['lot_id']?.toString() ?? '',
        kind: json['kind']?.toString() ?? '',
        title: json['title']?.toString() ?? '',
        body: json['body']?.toString() ?? '',
        createdAt: _time(json['created_at']),
        read: json['read_at'] != null,
      );
}
