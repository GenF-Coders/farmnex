import 'package:flutter/material.dart';

import '../core/network/route_api.dart';

/// A trip finished during this app session (the backend has no trip history list yet).
class FinishedTrip {
  final double distanceKm;
  final double earning;
  const FinishedTrip({required this.distanceKm, required this.earning});
}

/// The signed-in driver's vehicle, current trip and return-load offers
/// (`/api/v2/logistics` and `/api/v2/routes`).
class LogisticsProvider extends ChangeNotifier {
  final RouteApi _api = RouteApi();

  VehicleModel? _vehicle;
  TripModel? _trip;
  List<BackhaulOption> _backhaul = [];
  final List<FinishedTrip> _finished = [];

  bool _isLoading = false;
  bool _loaded = false;
  bool _busy = false;
  String? _error;

  VehicleModel? get vehicle => _vehicle;
  TripModel? get trip => _trip;
  List<BackhaulOption> get backhaul => List.unmodifiable(_backhaul);
  bool get isLoading => _isLoading;
  bool get hasLoaded => _loaded;
  bool get isBusy => _busy;
  String? get error => _error;

  bool get hasVehicle => _vehicle != null;
  bool get isOnline => _vehicle?.isOnline ?? false;
  String get vehicleStatus => _vehicle?.status ?? 'offline';

  List<FinishedTrip> get completedTrips => List.unmodifiable(_finished);
  double get earningsPaid => _finished.fold<double>(0, (sum, t) => sum + t.earning);
  double get earningsPending => _trip?.estimatedCost ?? 0;
  double get kmCovered => _finished.fold<double>(0, (sum, t) => sum + t.distanceKm);

  /// Loads the driver's vehicle, its running trip and (when free) return-load offers.
  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final vehicles = await _api.myVehicles();
      _vehicle = vehicles.isEmpty ? null : vehicles.first;
      await _refreshTripAndOffers();
      _loaded = true;
    } catch (e) {
      _error = routeErrorMessage(e);
    }
    _isLoading = false;
    notifyListeners();
  }

  /// Forget everything (logout / another driver logs in).
  void clear() {
    _vehicle = null;
    _trip = null;
    _backhaul = [];
    _finished.clear();
    _loaded = false;
    _error = null;
    notifyListeners();
  }

  Future<void> _refreshTripAndOffers() async {
    final v = _vehicle;
    if (v == null) {
      _trip = null;
      _backhaul = [];
      return;
    }
    _trip = await _api.currentTrip(v.id);
    _backhaul = (_trip == null && v.isOnline) ? await _api.backhaul(v.id) : [];
  }

  /// Runs one action, shows its busy state and returns null on success or a short error message.
  Future<String?> _run(Future<void> Function() action) async {
    _busy = true;
    notifyListeners();
    try {
      await action();
      return null;
    } catch (e) {
      return routeErrorMessage(e);
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<String?> registerVehicle({
    required String vehicleNumber,
    required String vehicleType,
    required double capacityKg,
    required double ratePerTonKm,
    required bool refrigerated,
    required double baseLat,
    required double baseLng,
    String? baseLabel,
  }) =>
      _run(() async {
        _vehicle = await _api.registerVehicle(
          vehicleNumber: vehicleNumber,
          vehicleType: vehicleType,
          capacityKg: capacityKg,
          ratePerTonKm: ratePerTonKm,
          refrigerated: refrigerated,
          baseLat: baseLat,
          baseLng: baseLng,
          baseLabel: baseLabel,
        );
      });

  Future<String?> toggleOnline() {
    final v = _vehicle;
    if (v == null || v.onTrip) return Future.value(null);
    return _run(() async {
      _vehicle = await _api.setStatus(v.id, online: !v.isOnline);
      _backhaul = (_trip == null && _vehicle!.isOnline) ? await _api.backhaul(v.id) : [];
    });
  }

  /// Lets the optimizer pool nearby pending loads into one trip.
  Future<String?> findLoads() {
    final v = _vehicle;
    if (v == null) return Future.value(null);
    return _run(() async {
      _trip = await _api.planTrip(v.id);
      _backhaul = [];
      await _reloadVehicle();
    });
  }

  Future<String?> acceptBackhaul(String loadId) {
    final v = _vehicle;
    if (v == null) return Future.value(null);
    return _run(() async {
      _trip = await _api.acceptLoad(v.id, loadId);
      _backhaul = [];
      await _reloadVehicle();
    });
  }

  Future<String?> startTrip() {
    final t = _trip;
    if (t == null) return Future.value(null);
    return _run(() async {
      _trip = await _api.startTrip(t.id);
    });
  }

  Future<String?> cancelTrip() {
    final t = _trip;
    if (t == null) return Future.value(null);
    return _run(() async {
      await _api.cancelTrip(t.id);
      _trip = null;
      await _reloadVehicle();
      await _refreshTripAndOffers();
    });
  }

  /// Marks a pickup or drop as done. The server releases the money when the last drop is done.
  Future<String?> completeStop(TripStop stop) {
    final t = _trip;
    if (t == null) return Future.value(null);
    return _run(() async {
      await _api.completeStop(t.id, stop.id);
      final fresh = await _api.currentTrip(_vehicle!.id);
      if (fresh == null) {
        _finished.add(FinishedTrip(distanceKm: t.totalDistanceKm, earning: t.estimatedCost));
        _trip = null;
        await _reloadVehicle();
        await _refreshTripAndOffers();
      } else {
        _trip = fresh;
      }
    });
  }

  /// GPS ping from the trip screen. Failures are ignored on purpose: the next ping retries.
  Future<void> sendPing(double lat, double lng, {double? speedKmph}) async {
    final v = _vehicle;
    if (v == null) return;
    try {
      await _api.ping(v.id, lat, lng, speedKmph: speedKmph);
    } catch (_) {}
  }

  Future<void> _reloadVehicle() async {
    final vehicles = await _api.myVehicles();
    _vehicle = vehicles.isEmpty ? null : vehicles.first;
  }
}
