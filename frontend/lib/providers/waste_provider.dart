import 'package:flutter/material.dart';

import '../core/network/farm_crop_api.dart';
import '../core/network/waste_api.dart';
import '../models/waste_model.dart';

/// Waste lots from the backend. No demo data: an empty list means nobody has listed waste yet.
class WasteProvider extends ChangeNotifier {
  final WasteApi _api = WasteApi();
  final FarmCropApi _farms = FarmCropApi();

  List<WasteItem> _items = [];
  bool _isLoading = false;
  bool _isListing = false;
  String? _error;

  List<WasteItem> get items => List.unmodifiable(_items);
  bool get isLoading => _isLoading;
  bool get isListing => _isListing;
  String? get error => _error;

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      _items = await _api.list();
    } catch (e) {
      _error = wasteErrorMessage(e);
    }
    _isLoading = false;
    notifyListeners();
  }

  /// Forget everything (someone logged out / another user logged in).
  void clear() {
    _items = [];
    _error = null;
    notifyListeners();
  }

  /// Lists the waste on the farmer's first farm. Returns null on success, else a message for the screen.
  Future<String?> createWasteListing({
    required String wasteType,
    required String utilizationType,
    required double quantity,
    required String unit,
    required double pricePerUnit,
  }) async {
    _isListing = true;
    notifyListeners();
    String? problem;
    try {
      final farms = await _farms.listMyFarms();
      if (farms.isEmpty) {
        problem = 'Add a farm first (My Crops), then list your waste.';
      } else {
        final item = await _api.create(
          farmId: farms.first.publicId,
          wasteType: wasteType,
          utilizationType: utilizationType,
          quantity: quantity,
          unit: unit,
          pricePerUnit: pricePerUnit,
        );
        _items = [item, ..._items];
      }
    } catch (e) {
      problem = wasteErrorMessage(e);
    }
    _isListing = false;
    notifyListeners();
    return problem;
  }
}
