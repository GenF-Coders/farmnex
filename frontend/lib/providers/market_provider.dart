import 'package:flutter/material.dart';
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

  List<CropItem> get crops => _crops;
  String get selectedCategory => _selectedCategory;
  String get searchQuery => _searchQuery;
  bool get isLoading => _isLoading;

  final List<String> categories = const [
    'All',
    'Grains',
    'Oilseeds',
    'Vegetables',
    'Fruits',
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

  MarketProvider() {
    _loadCrops();
  }

  Future<void> _loadCrops() async {
    _isLoading = true;
    notifyListeners();

    _crops = [
      const CropItem(
        id: 'crop-1',
        name: 'Sharbati Wheat (गेहूं)',
        category: 'Grains',
        variety: 'Grade A Gold',
        currentPrice: 2450,
        unit: 'Quintal',
        priceTrend: 4.2,
        expectedHarvestDate: '2 Days Left (Final Bidding Window)',
        daysToHarvest: 2,
        biddingActive: true,
        lastTwoDaysAIActive: true,
        expectedMinPrice: 2480,
        expectedMaxPrice: 2550,
        aiConfidence: 86,
        aiDemand: 'Very High',
        aiReasons: [
          'Heavy procurement demand from South Indian flour mills',
          'Recent mandi arrivals 18% lower than 5-year average',
          'Export quote surge in port hubs over the past 48 hours',
          'Optimal grain moisture content verified (11.5%)',
        ],
        quantityAvailable: 150,
        location: 'Indore Mandi, MP',
        farmerName: 'Ramesh Patil',
        emoji: '🌾',
        isPerishable: false,
      ),
      const CropItem(
        id: 'crop-2',
        name: 'Yellow Soybean (सोयाबीन)',
        category: 'Oilseeds',
        variety: 'JS-335 Organic',
        currentPrice: 4850,
        unit: 'Quintal',
        priceTrend: -1.5,
        expectedHarvestDate: '6 Days Left (Pre-Bidding Stage)',
        daysToHarvest: 6,
        biddingActive: true,
        lastTwoDaysAIActive: false,
        expectedMinPrice: 4800,
        expectedMaxPrice: 4950,
        aiConfidence: 78,
        aiDemand: 'High',
        aiReasons: [
          'Crush margins favorable for central edible oil refineries',
          'Arrivals picking up across Vidarbha and Malwa belts',
        ],
        quantityAvailable: 80,
        location: 'Latur, Maharashtra',
        farmerName: 'Balasaheb Shinde',
        emoji: '🌱',
        isPerishable: false,
      ),
      const CropItem(
        id: 'crop-3',
        name: 'Hybrid Tomato (टमाटर)',
        category: 'Vegetables',
        variety: 'Abhinav Red',
        currentPrice: 1800,
        unit: 'Crate (25kg)',
        priceTrend: -12.4,
        expectedHarvestDate: 'Urgent: Harvest Today!',
        daysToHarvest: 0,
        biddingActive: false,
        lastTwoDaysAIActive: false,
        aiDemand: 'Moderate',
        quantityAvailable: 350,
        location: 'Nashik, Maharashtra',
        farmerName: 'Sanjay Jadhav',
        emoji: '🍅',
        isPerishable: true,
      ),
      const CropItem(
        id: 'crop-4',
        name: 'Nashik Red Onion (प्याज)',
        category: 'Vegetables',
        variety: 'Garwa Export Quality',
        currentPrice: 2100,
        unit: 'Quintal',
        priceTrend: 6.8,
        expectedHarvestDate: '12 Days to Harvest',
        daysToHarvest: 12,
        biddingActive: false,
        lastTwoDaysAIActive: false,
        aiDemand: 'High',
        quantityAvailable: 220,
        location: 'Lasalgaon, Maharashtra',
        farmerName: 'Popatrao Pawar',
        emoji: '🧅',
        isPerishable: false,
      ),
      const CropItem(
        id: 'crop-5',
        name: 'Golden Mustard (सरसों)',
        category: 'Oilseeds',
        variety: 'Pusa Bold',
        currentPrice: 5400,
        unit: 'Quintal',
        priceTrend: 3.1,
        expectedHarvestDate: '4 Days Left (Pre-Bidding Stage)',
        daysToHarvest: 4,
        biddingActive: true,
        lastTwoDaysAIActive: false,
        expectedMinPrice: 5350,
        expectedMaxPrice: 5550,
        aiConfidence: 82,
        aiDemand: 'High',
        aiReasons: [
          'High oil content test results (41.2%)',
          'Winter consumption demand spike across North India',
        ],
        quantityAvailable: 95,
        location: 'Bharatpur, Rajasthan',
        farmerName: 'Ramkishan Sharma',
        emoji: '🌾',
        isPerishable: false,
      ),
      const CropItem(
        id: 'crop-6',
        name: 'Devgad Alphonso Mango (हापूस)',
        category: 'Fruits',
        variety: 'GI Tagged Devgad',
        currentPrice: 1200,
        unit: 'Dozen',
        priceTrend: 8.5,
        expectedHarvestDate: '1 Day Left (Final Bidding Window)',
        daysToHarvest: 1,
        biddingActive: true,
        lastTwoDaysAIActive: true,
        expectedMinPrice: 1250,
        expectedMaxPrice: 1400,
        aiConfidence: 92,
        aiDemand: 'Very High',
        aiReasons: [
          'Strong export demand for Gulf shipment flights',
          'Premium Brix sugar level reading 19.5',
        ],
        quantityAvailable: 500,
        location: 'Ratnagiri, Maharashtra',
        farmerName: 'Dattaram Parab',
        emoji: '🥭',
        isPerishable: true,
      ),
    ];

    _isLoading = false;
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
    return _crops.where((crop) {
      final matchesSearch = crop.name.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          crop.location.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          crop.variety.toLowerCase().contains(_searchQuery.toLowerCase());
      final matchesCategory = _selectedCategory == 'All' || crop.category == _selectedCategory;
      return matchesSearch && matchesCategory;
    }).toList();
  }

  CropItem? getCropById(String id) {
    try {
      return _crops.firstWhere((c) => c.id == id);
    } catch (_) {
      return null;
    }
  }
}
