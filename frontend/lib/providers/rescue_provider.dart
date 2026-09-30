import 'package:flutter/material.dart';

import '../core/network/crop_rescue_api.dart';
import '../models/rescue_listing_model.dart';

/// Crop Rescue state for a farmer: their lots, the alerts about them, and the crop catalog.
/// Every call goes to `/api/v2/rescue/...`; there is no demo data.
class RescueProvider extends ChangeNotifier {
  final CropRescueApi _api;

  RescueProvider([CropRescueApi? api]) : _api = api ?? CropRescueApi();

  bool _isLoading = false;
  bool _loaded = false;
  bool _saving = false;
  String? _errorMessage;
  String _searchQuery = '';

  List<RescueLot> _lots = const [];
  List<RescueCrop> _crops = const [];
  List<RescueAlert> _alerts = const [];

  bool get isLoading => _isLoading;
  bool get loaded => _loaded;
  bool get isSaving => _saving;
  String? get errorMessage => _errorMessage;
  String get searchQuery => _searchQuery;
  List<RescueCrop> get crops => _crops;
  List<RescueAlert> get alerts => _alerts;
  List<RescueAlert> get unreadAlerts => _alerts.where((a) => !a.read).toList();

  /// The farmer's lots, most urgent first (least time left), finished lots last.
  List<RescueLot> get lots {
    final q = _searchQuery.trim().toLowerCase();
    final list = _lots.where((l) => q.isEmpty || cropName(l.cropCode).toLowerCase().contains(q)).toList();
    list.sort((a, b) {
      if (a.isOpen != b.isOpen) return a.isOpen ? -1 : 1;
      return (a.remainingHours ?? double.infinity).compareTo(b.remainingHours ?? double.infinity);
    });
    return list;
  }

  int get openCount => _lots.where((l) => l.isOpen).length;
  int get atRiskCount => _lots.where((l) => l.isAtRisk).length;
  int get soldCount => _lots.where((l) => l.status == 'SOLD').length;

  RescueLot? byId(String id) {
    for (final lot in _lots) {
      if (lot.id == id) return lot;
    }
    return null;
  }

  String cropName(String code) {
    for (final crop in _crops) {
      if (crop.code == code) return crop.nameEn;
    }
    return code.isEmpty ? code : code[0].toUpperCase() + code.substring(1);
  }

  void setSearch(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  /// Loads lots, the crop list and alerts. Safe to call again (pull to refresh, retry).
  Future<void> load() async {
    if (_isLoading) return;
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final results = await Future.wait([_api.lots(), _api.crops(), _api.alerts()]);
      _lots = results[0] as List<RescueLot>;
      _crops = results[1] as List<RescueCrop>;
      _alerts = results[2] as List<RescueAlert>;
      _loaded = true;
    } catch (e) {
      _errorMessage = rescueErrorMessage(e);
    }
    _isLoading = false;
    notifyListeners();
  }

  /// Quiet refresh for the 30-second poll: lots and alerts only, never shows an error.
  Future<void> refreshAlerts() async {
    try {
      final results = await Future.wait([_api.alerts(), _api.lots()]);
      _alerts = results[0] as List<RescueAlert>;
      _lots = results[1] as List<RescueLot>;
      notifyListeners();
    } catch (_) {
      // A missed poll is fine; the next one tries again.
    }
  }

  /// Registers a lot at the farmer's farm location. Returns null and sets [errorMessage] on failure.
  Future<RescueLot?> registerLot({
    required String cropCode,
    required double quantityKg,
    required DateTime harvestedAt,
    String storageMode = 'ambient',
    double floorPricePerKg = 0,
  }) async {
    if (quantityKg <= 0 || cropCode.isEmpty) {
      _errorMessage = 'Please choose a crop and enter the quantity.';
      notifyListeners();
      return null;
    }
    _saving = true;
    _errorMessage = null;
    notifyListeners();
    try {
      final place = await _api.farmLocation();
      if (place == null) {
        _errorMessage = 'Add your farm location first (Profile → My farms), then register the lot.';
        return null;
      }
      final lot = await _api.createLot(
        cropCode: cropCode,
        quantityKg: quantityKg,
        harvestedAt: harvestedAt,
        lat: place.lat,
        lng: place.lng,
        storageMode: storageMode,
        floorPricePerKg: floorPricePerKg,
      );
      _lots = [lot, ..._lots];
      return lot;
    } catch (e) {
      _errorMessage = rescueErrorMessage(e);
      return null;
    } finally {
      _saving = false;
      notifyListeners();
    }
  }

  /// Used by the voice assistant dialog, which collects a crop name, quantity and price.
  /// Only the fields Crop Rescue understands are used; the lot is treated as harvested now.
  Future<RescueLot?> publish({
    required String cropName,
    required String category,
    required String emoji,
    required double quantity,
    required String unit,
    required double pricePerUnit,
    required String location,
    required DateTime sellBy,
    required String farmerId,
    required String farmerName,
    String description = '',
    String imageUrl = '',
  }) async {
    if (_crops.isEmpty) await load();
    final wanted = cropName.trim().toLowerCase();
    String? code;
    for (final crop in _crops) {
      if (crop.code == wanted || crop.nameEn.toLowerCase() == wanted) code = crop.code;
    }
    if (code == null) {
      _errorMessage = 'Crop Rescue does not cover this crop yet.';
      notifyListeners();
      return null;
    }
    final kg = switch (unit.toLowerCase()) {
      'quintal' => quantity * 100,
      'ton' => quantity * 1000,
      _ => quantity,
    };
    return registerLot(
      cropCode: code,
      quantityKg: kg,
      harvestedAt: DateTime.now(),
      floorPricePerKg: unit.toLowerCase() == 'kg' ? pricePerUnit : 0,
    );
  }

  /// The lot with its check history. Replaces the copy in the list.
  Future<RescueLot?> loadDetail(String id) async {
    try {
      final lot = await _api.lot(id);
      _replace(lot);
      notifyListeners();
      return lot;
    } catch (e) {
      _errorMessage = rescueErrorMessage(e);
      notifyListeners();
      return null;
    }
  }

  /// Ranked buyers for an at-risk lot. Throws so the detail screen can show its own message.
  Future<List<RescueMatch>> matchesFor(String lotId) => _api.matches(lotId);

  Future<bool> markSold(String lotId) async {
    _saving = true;
    _errorMessage = null;
    notifyListeners();
    try {
      _replace(await _api.markSold(lotId));
      return true;
    } catch (e) {
      _errorMessage = rescueErrorMessage(e);
      return false;
    } finally {
      _saving = false;
      notifyListeners();
    }
  }

  /// Demo: moves this lot's clock forward so an alert appears without waiting.
  Future<bool> fastForward(String lotId, double hours) async {
    _saving = true;
    _errorMessage = null;
    notifyListeners();
    try {
      await _api.simulate(hours: hours, lotId: lotId);
      await loadDetail(lotId);
      await refreshAlerts();
      return true;
    } catch (e) {
      _errorMessage = rescueErrorMessage(e);
      return false;
    } finally {
      _saving = false;
      notifyListeners();
    }
  }

  Future<void> markAlertRead(String alertId) async {
    try {
      await _api.markAlertRead(alertId);
      _alerts = [
        for (final a in _alerts)
          if (a.id == alertId)
            RescueAlert(
              id: a.id,
              lotId: a.lotId,
              kind: a.kind,
              title: a.title,
              body: a.body,
              createdAt: a.createdAt,
              read: true,
            )
          else
            a,
      ];
      notifyListeners();
    } catch (_) {
      // Stays unread; it shows again on the next poll.
    }
  }

  void _replace(RescueLot lot) {
    final index = _lots.indexWhere((l) => l.id == lot.id);
    _lots = index == -1 ? [lot, ..._lots] : [..._lots]..[index] = lot;
  }
}
