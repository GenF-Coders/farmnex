import 'package:flutter/material.dart';

import '../core/network/farm_crop_api.dart';
import '../core/network/listing_api.dart';
import '../models/crop_model.dart';
import '../models/listing_model.dart';

/// The signed-in farmer's own lots (`GET /product-listings?mine=true`).
class ListingProvider extends ChangeNotifier {
  final ListingApi _api = ListingApi();
  final FarmCropApi _setup = FarmCropApi();

  List<CropItem> _listings = [];
  bool _isLoading = false;
  bool _loaded = false;
  String? _error;

  List<CropItem> get listings => List.unmodifiable(_listings);
  List<CropItem> get activeListings => _listings.where((c) => c.status == 'active').toList();
  bool get isLoading => _isLoading;
  bool get hasLoaded => _loaded;
  String? get error => _error;

  double get inventoryValue => _listings
      .where((c) => c.status == 'active')
      .fold<double>(0, (sum, c) => sum + c.currentPrice * c.quantityAvailable);

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final rows = await _api.list(mine: true);
      _listings = rows.map((r) => r.toCropItem()).toList();
      _loaded = true;
    } catch (e) {
      _error = listingErrorMessage(e);
    }
    _isLoading = false;
    notifyListeners();
  }

  /// Forget everything (used when someone logs out / another farmer logs in).
  void clear() {
    _listings = [];
    _loaded = false;
    _error = null;
    notifyListeners();
  }

  Future<List<CropTypeModel>> cropTypes() => _setup.listCropTypes();
  Future<List<FarmSummary>> myFarms() => _setup.listMyFarms();

  Future<FarmSummary> createFarm({
    required String farmName,
    required String addressLine1,
    required String city,
    required String district,
    required String state,
    required String postalCode,
  }) =>
      _setup.createFarm(
        farmName: farmName,
        addressLine1: addressLine1,
        city: city,
        district: district,
        state: state,
        postalCode: postalCode,
      );

  /// farm crop → crop batch → listing. Returns null on success, or a short error message.
  Future<String?> addListing({
    required String farmId,
    required CropTypeModel cropType,
    required double price,
    required double quantity,
    required String grade,
    required bool preBid,
    bool isOrganic = false,
  }) async {
    try {
      final batchId = await _setup.createFarmCropAndBatch(
        farmId: farmId,
        cropTypeId: cropType.publicId,
        quantity: quantity,
        unit: cropType.defaultUnit,
        qualityGrade: grade,
        organic: isOrganic,
      );
      await _api.create(
        farmId: farmId,
        cropBatchId: batchId,
        title: cropType.name,
        description: grade,
        listingType: preBid ? 'PRE_BID' : 'FIXED_PRICE',
        price: price,
        quantity: quantity,
        unit: cropType.defaultUnit,
      );
      await load();
      return null;
    } catch (e) {
      return listingErrorMessage(e);
    }
  }

  /// Returns null on success, or a short error message.
  Future<String?> updatePrice(String id, double price) async {
    if (price <= 0) return 'Enter a price above zero.';
    try {
      final row = await _api.updatePrice(id, price);
      final index = _listings.indexWhere((c) => c.id == id);
      if (index != -1) {
        _listings[index] = row.toCropItem();
        notifyListeners();
      }
      return null;
    } catch (e) {
      return listingErrorMessage(e);
    }
  }

  /// Closes the lot on the backend (it stays in the list as "closed").
  Future<String?> remove(String id) async {
    try {
      await _api.close(id);
      await load();
      return null;
    } catch (e) {
      return listingErrorMessage(e);
    }
  }
}
