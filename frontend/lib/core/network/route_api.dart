import 'package:dio/dio.dart';

import '../config/api_config.dart';
import 'api_client.dart';

/// Driver vehicles, trips and delivery tracking (`/api/v2/logistics` and `/api/v2/routes`).
/// Identity comes from the login token; nothing here sends a driver or owner id.
class RouteApi {
  static final RouteApi _instance = RouteApi._();
  factory RouteApi() => _instance;
  RouteApi._();

  final Dio _dio = ApiClient().dio;

  Future<List<VehicleModel>> myVehicles() async {
    final r = await _dio.get<dynamic>(ApiConfig.logisticsMyVehiclesEndpoint);
    return (r.data as List<dynamic>)
        .map((e) => VehicleModel.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<VehicleModel> registerVehicle({
    required String vehicleNumber,
    required String vehicleType,
    required double capacityKg,
    required double ratePerTonKm,
    required bool refrigerated,
    required double baseLat,
    required double baseLng,
    String? baseLabel,
  }) async {
    final r = await _dio.post<dynamic>(ApiConfig.logisticsVehiclesEndpoint, data: {
      'vehicle_number': vehicleNumber,
      'vehicle_type': vehicleType,
      'capacity_kg': capacityKg,
      'rate_per_ton_km': ratePerTonKm,
      'refrigerated': refrigerated,
      'base_lat': baseLat,
      'base_lng': baseLng,
      if (baseLabel != null && baseLabel.isNotEmpty) 'base_label': baseLabel,
    });
    return VehicleModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<VehicleModel> setStatus(String vehicleId, {required bool online}) async {
    final r = await _dio.patch<dynamic>(
      ApiConfig.routesVehicleStatusEndpoint(vehicleId),
      data: {'status': online ? 'available' : 'offline'},
    );
    return VehicleModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<void> ping(String vehicleId, double lat, double lng, {double? speedKmph}) async {
    await _dio.post<dynamic>(ApiConfig.routesVehicleLocationEndpoint(vehicleId), data: {
      'lat': lat,
      'lng': lng,
      if (speedKmph != null && speedKmph >= 0) 'speed_kmph': speedKmph,
    });
  }

  Future<TripModel?> currentTrip(String vehicleId) async {
    final r = await _dio.get<dynamic>(ApiConfig.routesVehicleTripEndpoint(vehicleId));
    final data = r.data;
    return data is Map<String, dynamic> ? TripModel.fromJson(data) : null;
  }

  /// Lets the optimizer pool nearby pending loads for this vehicle.
  Future<TripModel> planTrip(String vehicleId) async {
    final r = await _dio.post<dynamic>(ApiConfig.routesPlanTripEndpoint, data: {'vehicle_id': vehicleId});
    return TripModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<List<BackhaulOption>> backhaul(String vehicleId) async {
    final r = await _dio.get<dynamic>(ApiConfig.routesVehicleBackhaulEndpoint(vehicleId));
    final options = (r.data as Map<String, dynamic>)['options'] as List<dynamic>? ?? const [];
    return options.map((e) => BackhaulOption.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<TripModel> acceptLoad(String vehicleId, String loadId) async {
    final r = await _dio.post<dynamic>(ApiConfig.routesAcceptLoadEndpoint(vehicleId, loadId));
    return TripModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<TripModel> startTrip(String tripId) async {
    final r = await _dio.post<dynamic>(ApiConfig.routesTripStartEndpoint(tripId));
    return TripModel.fromJson(r.data as Map<String, dynamic>);
  }

  Future<void> cancelTrip(String tripId) async {
    await _dio.post<dynamic>(ApiConfig.routesTripCancelEndpoint(tripId));
  }

  Future<void> completeStop(String tripId, String stopId) async {
    await _dio.post<dynamic>(ApiConfig.routesStopCompleteEndpoint(tripId, stopId));
  }

  /// Delivery status for one order (buyer / farmer). Null when the order has no delivery yet.
  Future<OrderDelivery?> orderDelivery(String orderPublicId) async {
    try {
      final r = await _dio.get<dynamic>(ApiConfig.routesOrderDeliveryEndpoint(orderPublicId));
      return OrderDelivery.fromJson(r.data as Map<String, dynamic>);
    } on DioException catch (e) {
      if (e.response?.statusCode == 404) return null;
      rethrow;
    }
  }
}

/// A short, plain message for the screens (never the raw exception text).
String routeErrorMessage(Object error) {
  if (error is DioException) {
    final code = error.response?.statusCode;
    final data = error.response?.data;
    final detail = data is Map ? data['detail'] : null;
    if (detail is String && detail.isNotEmpty && code != null && code < 500 && code != 401) {
      return detail;
    }
    if (code == 401) return 'Please log in again.';
    if (code == 404) return 'Not found.';
    if (error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return 'No connection. Check your internet and try again.';
    }
  }
  return 'Something went wrong. Please try again.';
}

double _num(dynamic v) => (v as num?)?.toDouble() ?? 0;

class VehicleModel {
  final String id;
  final String vehicleNumber;
  final String vehicleType;
  final double capacityKg;
  final bool refrigerated;
  final double ratePerTonKm;
  final String baseLabel;
  final String status; // available | on_trip | offline

  const VehicleModel({
    required this.id,
    required this.vehicleNumber,
    required this.vehicleType,
    required this.capacityKg,
    required this.refrigerated,
    required this.ratePerTonKm,
    required this.baseLabel,
    required this.status,
  });

  factory VehicleModel.fromJson(Map<String, dynamic> j) => VehicleModel(
        id: j['id'].toString(),
        vehicleNumber: (j['vehicle_number'] ?? '').toString(),
        vehicleType: (j['vehicle_type'] ?? '').toString(),
        capacityKg: _num(j['capacity_kg']),
        refrigerated: j['refrigerated'] == true,
        ratePerTonKm: _num(j['rate_per_ton_km']),
        baseLabel: (j['base_label'] ?? '').toString(),
        status: (j['status'] ?? 'offline').toString(),
      );

  bool get isOnline => status == 'available' || status == 'on_trip';
  bool get onTrip => status == 'on_trip';
}

class TripStop {
  final String id;
  final int seq;
  final String kind; // pickup | drop
  final String loadId;
  final String label;
  final String status; // pending | done

  const TripStop({
    required this.id,
    required this.seq,
    required this.kind,
    required this.loadId,
    required this.label,
    required this.status,
  });

  factory TripStop.fromJson(Map<String, dynamic> j) => TripStop(
        id: j['id'].toString(),
        seq: (j['seq'] as num?)?.toInt() ?? 0,
        kind: (j['kind'] ?? '').toString(),
        loadId: (j['load_id'] ?? '').toString(),
        label: (j['label'] ?? '').toString(),
        status: (j['status'] ?? 'pending').toString(),
      );

  bool get isDone => status == 'done';
  bool get isPickup => kind == 'pickup';
}

class TripModel {
  final String id;
  final String status; // planned | in_progress | completed | cancelled
  final bool isBackhaul;
  final double totalDistanceKm;
  final double totalDurationMin;
  final double estimatedCost;
  final List<TripStop> stops;
  final String? trackingUrl;

  const TripModel({
    required this.id,
    required this.status,
    required this.isBackhaul,
    required this.totalDistanceKm,
    required this.totalDurationMin,
    required this.estimatedCost,
    required this.stops,
    this.trackingUrl,
  });

  factory TripModel.fromJson(Map<String, dynamic> j) => TripModel(
        id: j['id'].toString(),
        status: (j['status'] ?? '').toString(),
        isBackhaul: j['is_backhaul'] == true,
        totalDistanceKm: _num(j['total_distance_km']),
        totalDurationMin: _num(j['total_duration_min']),
        estimatedCost: _num(j['estimated_cost']),
        stops: ((j['stops'] as List<dynamic>?) ?? const [])
            .map((e) => TripStop.fromJson(e as Map<String, dynamic>))
            .toList()
          ..sort((a, b) => a.seq.compareTo(b.seq)),
        trackingUrl: j['tracking_url'] as String?,
      );

  bool get isPlanned => status == 'planned';
  bool get isRunning => status == 'in_progress';
  bool get isCompleted => status == 'completed';

  TripStop? get nextStop {
    for (final s in stops) {
      if (!s.isDone) return s;
    }
    return null;
  }
}

class BackhaulOption {
  final String loadId;
  final String crop;
  final double weightKg;
  final String pickupAddress;
  final String dropAddress;
  final double distanceToPickupKm;
  final double loadedKm;
  final double emptyKmSaved;
  final double estimatedEarning;

  const BackhaulOption({
    required this.loadId,
    required this.crop,
    required this.weightKg,
    required this.pickupAddress,
    required this.dropAddress,
    required this.distanceToPickupKm,
    required this.loadedKm,
    required this.emptyKmSaved,
    required this.estimatedEarning,
  });

  factory BackhaulOption.fromJson(Map<String, dynamic> j) => BackhaulOption(
        loadId: j['load_id'].toString(),
        crop: (j['crop'] ?? '').toString(),
        weightKg: _num(j['weight_kg']),
        pickupAddress: (j['pickup_address'] ?? '').toString(),
        dropAddress: (j['drop_address'] ?? '').toString(),
        distanceToPickupKm: _num(j['distance_to_pickup_km']),
        loadedKm: _num(j['loaded_km']),
        emptyKmSaved: _num(j['empty_km_saved']),
        estimatedEarning: _num(j['estimated_earning']),
      );
}

/// What the buyer / farmer sees for one order: status, fare, truck, ETA and the tracking link.
class OrderDelivery {
  final String status; // pending | assigned | picked_up | delivered | cancelled
  final double? estimatedFare;
  final String? trackingUrl;
  final String? vehicleNumber;
  final double? etaMin; // minutes until the drop, when known

  const OrderDelivery({
    required this.status,
    this.estimatedFare,
    this.trackingUrl,
    this.vehicleNumber,
    this.etaMin,
  });

  factory OrderDelivery.fromJson(Map<String, dynamic> j) {
    final vehicle = j['vehicle'] is Map ? Map<String, dynamic>.from(j['vehicle'] as Map) : const <String, dynamic>{};
    final drop = j['delivery'] is Map ? Map<String, dynamic>.from(j['delivery'] as Map) : const <String, dynamic>{};
    return OrderDelivery(
      status: (j['status'] ?? '').toString(),
      estimatedFare: (j['estimated_fare'] as num?)?.toDouble(),
      trackingUrl: j['tracking_url'] as String?,
      vehicleNumber: vehicle['vehicle_number']?.toString(),
      etaMin: (drop['eta_min'] as num?)?.toDouble(),
    );
  }

  bool get isDelivered => status == 'delivered';
  bool get canTrack => (trackingUrl ?? '').isNotEmpty && !isDelivered && status != 'cancelled';
}
