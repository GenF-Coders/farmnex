import 'package:flutter/material.dart';

import '../models/rescue_listing_model.dart';

class RescueProvider extends ChangeNotifier {
  bool _isLoading = false;
  String? _errorKey;

  String _searchQuery = '';
  String _categoryFilter = 'all';
  String _sortBy = 'urgent';

  bool get isLoading => _isLoading;
  String? get errorKey => _errorKey;
  String get searchQuery => _searchQuery;
  String get categoryFilter => _categoryFilter;
  String get sortBy => _sortBy;

  static const List<String> categories = [
    'all',
    'cat_vegetables',
    'cat_fruits',
    'cat_grains',
    'cat_pulses',
    'cat_others',
  ];

  static const Map<String, String> categorySymbols = {
    'all': '🧺',
    'cat_vegetables': '🥦',
    'cat_fruits': '🍎',
    'cat_grains': '🌾',
    'cat_pulses': '🫘',
    'cat_others': '🌱',
  };

  final List<RescueListing> _listings = [
    RescueListing(
      id: 'rsc-1',
      cropName: 'Tomato',
      category: 'cat_vegetables',
      emoji: '🍅',
      quantity: 500,
      unit: 'kg',
      pricePerUnit: 25,
      location: 'Pune, Maharashtra',
      sellBy: DateTime.now().add(const Duration(days: 2)),
      description: 'Fresh picked, grade A, ready for immediate pickup.',
      farmerId: 'usr-farmer-01',
      farmerName: 'Ramesh Patil',
      soldQuantity: 120,
      orderCount: 3,
      publishedAt: DateTime.now().subtract(const Duration(hours: 5)),
    ),
    RescueListing(
      id: 'rsc-2',
      cropName: 'Onion',
      category: 'cat_vegetables',
      emoji: '🧅',
      quantity: 800,
      unit: 'kg',
      pricePerUnit: 18,
      location: 'Nashik, Maharashtra',
      sellBy: DateTime.now().add(const Duration(days: 4)),
      description: 'Red onion, medium size, well dried.',
      farmerId: 'usr-farmer-02',
      farmerName: 'Sunil Bhosale',
      soldQuantity: 200,
      orderCount: 2,
      publishedAt: DateTime.now().subtract(const Duration(days: 1)),
    ),
    RescueListing(
      id: 'rsc-3',
      cropName: 'Banana',
      category: 'cat_fruits',
      emoji: '🍌',
      quantity: 300,
      unit: 'kg',
      pricePerUnit: 22,
      location: 'Jalgaon, Maharashtra',
      sellBy: DateTime.now().add(const Duration(days: 1)),
      description: 'Ripening fast, best sold today or tomorrow.',
      farmerId: 'usr-farmer-03',
      farmerName: 'Anita Deshmukh',
      publishedAt: DateTime.now().subtract(const Duration(hours: 9)),
    ),
    RescueListing(
      id: 'rsc-4',
      cropName: 'Green Chilli',
      category: 'cat_vegetables',
      emoji: '🌶️',
      quantity: 150,
      unit: 'kg',
      pricePerUnit: 40,
      location: 'Solapur, Maharashtra',
      sellBy: DateTime.now().add(const Duration(days: 5)),
      description: 'Spicy variety, freshly harvested.',
      farmerId: 'usr-farmer-04',
      farmerName: 'Kailas Jadhav',
      publishedAt: DateTime.now().subtract(const Duration(days: 2)),
    ),
    RescueListing(
      id: 'rsc-5',
      cropName: 'Potato',
      category: 'cat_vegetables',
      emoji: '🥔',
      quantity: 1000,
      unit: 'kg',
      pricePerUnit: 14,
      location: 'Indore, Madhya Pradesh',
      sellBy: DateTime.now().add(const Duration(days: 6)),
      description: 'Bulk lot, transport can be arranged.',
      farmerId: 'usr-farmer-05',
      farmerName: 'Balasaheb Shinde',
      soldQuantity: 1000,
      orderCount: 6,
      status: 'sold_out',
      publishedAt: DateTime.now().subtract(const Duration(days: 3)),
    ),
  ];

  List<RescueListing> get availableListings =>
      _listings.where((l) => l.isAvailable).toList();

  List<RescueListing> get filteredListings {
    var result = availableListings;

    if (_categoryFilter != 'all') {
      result = result.where((l) => l.category == _categoryFilter).toList();
    }

    if (_searchQuery.trim().isNotEmpty) {
      final q = _searchQuery.toLowerCase().trim();
      result = result
          .where((l) =>
              l.cropName.toLowerCase().contains(q) ||
              l.location.toLowerCase().contains(q) ||
              l.farmerName.toLowerCase().contains(q))
          .toList();
    }

    switch (_sortBy) {
      case 'price_low':
        result.sort((a, b) => a.pricePerUnit.compareTo(b.pricePerUnit));
        break;
      case 'price_high':
        result.sort((a, b) => b.pricePerUnit.compareTo(a.pricePerUnit));
        break;
      case 'newest':
        result.sort((a, b) => b.publishedAt.compareTo(a.publishedAt));
        break;
      default:
        result.sort((a, b) => a.daysLeft.compareTo(b.daysLeft));
    }

    return result;
  }

  void setSearch(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  void setCategory(String category) {
    _categoryFilter = category;
    notifyListeners();
  }

  void setSort(String sort) {
    _sortBy = sort;
    notifyListeners();
  }

  void clearFilters() {
    _searchQuery = '';
    _categoryFilter = 'all';
    _sortBy = 'urgent';
    notifyListeners();
  }

  RescueListing? byId(String id) {
    for (final listing in _listings) {
      if (listing.id == id) return listing;
    }
    return null;
  }

  List<RescueListing> listingsForFarmer(String farmerId) =>
      _listings.where((l) => l.farmerId == farmerId).toList();

  double earningsForFarmer(String farmerId) => _listings
      .where((l) => l.farmerId == farmerId)
      .fold<double>(0, (sum, l) => sum + l.soldQuantity * l.pricePerUnit);

  Future<RescueListing?> publish({
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
    if (cropName.trim().isEmpty || quantity <= 0 || pricePerUnit <= 0) {
      _errorKey = 'err_fill_required';
      notifyListeners();
      return null;
    }

    _isLoading = true;
    _errorKey = null;
    notifyListeners();

    try {

      await Future<void>.delayed(const Duration(milliseconds: 500));

      final listing = RescueListing(
        id: 'rsc-${DateTime.now().millisecondsSinceEpoch}',
        cropName: cropName.trim(),
        category: category,
        emoji: emoji,
        quantity: quantity,
        unit: unit,
        pricePerUnit: pricePerUnit,
        location: location,
        sellBy: sellBy,
        description: description,
        imageUrl: imageUrl,
        farmerId: farmerId,
        farmerName: farmerName,
        publishedAt: DateTime.now(),
      );

      _listings.insert(0, listing);
      _isLoading = false;
      notifyListeners();
      return listing;
    } catch (_) {
      _errorKey = 'err_generic';
      _isLoading = false;
      notifyListeners();
      return null;
    }
  }

  void updateListing(
    String id, {
    double? pricePerUnit,
    double? quantity,
    DateTime? sellBy,
    String? description,
  }) {
    final index = _listings.indexWhere((l) => l.id == id);
    if (index == -1) return;
    _listings[index] = _listings[index].copyWith(
      pricePerUnit: pricePerUnit,
      quantity: quantity,
      sellBy: sellBy,
      description: description,
    );
    notifyListeners();
  }

  void togglePause(String id) {
    final index = _listings.indexWhere((l) => l.id == id);
    if (index == -1) return;
    final current = _listings[index];
    if (current.status == 'sold_out') return;
    _listings[index] = current.copyWith(
      status: current.status == 'paused' ? 'active' : 'paused',
    );
    notifyListeners();
  }

  void deleteListing(String id) {
    _listings.removeWhere((l) => l.id == id);
    notifyListeners();
  }

  void recordSale(String id, double quantitySold) {
    final index = _listings.indexWhere((l) => l.id == id);
    if (index == -1) return;
    final current = _listings[index];
    final sold = current.soldQuantity + quantitySold;
    _listings[index] = current.copyWith(
      soldQuantity: sold > current.quantity ? current.quantity : sold,
      orderCount: current.orderCount + 1,
      status: sold >= current.quantity ? 'sold_out' : current.status,
    );
    notifyListeners();
  }

  void clearError() {
    _errorKey = null;
    notifyListeners();
  }
}
