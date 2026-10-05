import 'package:flutter/material.dart';
import '../core/network/listing_api.dart';
import '../models/crop_model.dart';

class MandiTickerItem {
  final String cropName;
  final String mandi;
  final double price;
  final String unit;
  final double trend;

  const MandiTickerItem({
    required this.cropName,
    required this.mandi,
    required this.price,
    required this.unit,
    required this.trend,
  });
}

class MarketProvider extends ChangeNotifier {
  List<CropItem> _crops = [];
  String _selectedCategory = 'All';
  String _searchQuery = '';
  bool _isLoading = false;
  bool _requested = false;
  String? _error;
  final ListingApi _api = ListingApi();

  List<CropItem> get crops {
    if (!_requested && !_isLoading) {
      _requested = true;
      Future.microtask(load);
    }
    return _crops;
  }

  String get selectedCategory => _selectedCategory;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get hasLoaded => _requested && !_isLoading;

  final List<String> categories = const [
    'All',
    'Grains',
    'Oilseeds',
    'Vegetables',
    'Fruits',
    'Other',
  ];

  final List<MandiTickerItem> mandiTicker = const [
    MandiTickerItem(
      cropName: 'Wheat (गेहूं)',
      mandi: 'Lasalgaon',
      price: 2450,
      unit: 'q',
      trend: 4.2,
    ),
    MandiTickerItem(
      cropName: 'Onion (प्याज)',
      mandi: 'Nashik',
      price: 2100,
      unit: 'q',
      trend: 6.8,
    ),
    MandiTickerItem(
      cropName: 'Soybean (सोयाबीन)',
      mandi: 'Indore APMC',
      price: 4850,
      unit: 'q',
      trend: -1.5,
    ),
    MandiTickerItem(
      cropName: 'Tomato (टमाटर)',
      mandi: 'Kolar Mandi',
      price: 1800,
      unit: 'crate',
      trend: -12.4,
    ),
  ];

  /// The crops list is loaded the first time something reads it (after login), or by [load].
  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final rows = await _api.list();
      _crops = rows.map((r) => r.toCropItem()).toList();
    } catch (e) {
      _error = listingErrorMessage(e);
    }
    _requested = true;
    _isLoading = false;
    notifyListeners();
  }

  /// Forget everything (log-out / another user logs in).
  void clear() {
    _crops = [];
    _error = null;
    _requested = false;
    notifyListeners();
  }

  void setCategory(String category) {
    _selectedCategory = category;
    notifyListeners();
  }

  void setSearchQuery(String query) {
    _searchQuery = query;
    notifyListeners();
  }

  List<CropItem> get filteredCrops {
    return crops.where((crop) {
      final matchesSearch = crop.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          crop.location.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          crop.variety.toLowerCase().contains(_searchQuery.toLowerCase());
      final matchesCategory = _selectedCategory == 'All' || crop.category == _selectedCategory;
      return matchesSearch && matchesCategory;
    }).toList();
  }

  CropItem? getCropById(String id) {
    try {
      return crops.firstWhere((c) => c.id == id);
    } catch (_) {
      return null;
    }
  }
}
