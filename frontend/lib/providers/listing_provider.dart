import 'package:flutter/material.dart';

import '../models/crop_model.dart';

class ListingProvider extends ChangeNotifier {
  final List<CropItem> _listings = [
    const CropItem(
      id: 'lot-1',
      name: 'Sharbati Wheat (गेहूं)',
      category: 'Grains',
      variety: 'Grade A Gold',
      currentPrice: 2450,
      unit: 'Quintal',
      priceTrend: 4.2,
      expectedHarvestDate: '2 Days Left',
      daysToHarvest: 2,
      biddingActive: true,
      lastTwoDaysAIActive: true,
      quantityAvailable: 150,
      location: 'Indore Mandi, MP',
      farmerName: 'Ramesh Patil',
      emoji: '🌾',
      status: 'active',
      grade: 'Grade A',
      views: 412,
      bidsCount: 7,
      ordersCount: 2,
      rating: 4.7,
      ratingCount: 31,
    ),
    const CropItem(
      id: 'lot-2',
      name: 'Yellow Soybean (सोयाबीन)',
      category: 'Oilseeds',
      variety: 'JS-335 Organic',
      currentPrice: 4850,
      unit: 'Quintal',
      priceTrend: -1.5,
      expectedHarvestDate: '6 Days Left',
      daysToHarvest: 6,
      biddingActive: true,
      lastTwoDaysAIActive: false,
      quantityAvailable: 60,
      location: 'Indore Mandi, MP',
      farmerName: 'Ramesh Patil',
      emoji: '🌱',
      status: 'active',
      grade: 'Grade A',
      isOrganic: true,
      views: 188,
      bidsCount: 3,
      ordersCount: 1,
      rating: 4.5,
      ratingCount: 12,
    ),
    const CropItem(
      id: 'lot-3',
      name: 'Desi Chana (चना)',
      category: 'Grains',
      variety: 'Kabuli Bold',
      currentPrice: 5600,
      unit: 'Quintal',
      priceTrend: 2.1,
      expectedHarvestDate: 'Harvested',
      daysToHarvest: 0,
      biddingActive: false,
      lastTwoDaysAIActive: false,
      quantityAvailable: 0,
      location: 'Indore Mandi, MP',
      farmerName: 'Ramesh Patil',
      emoji: '🫘',
      status: 'sold_out',
      grade: 'Grade B',
      views: 96,
      bidsCount: 5,
      ordersCount: 5,
      rating: 4.3,
      ratingCount: 9,
    ),
  ];

  List<CropItem> get listings => List.unmodifiable(_listings);

  List<CropItem> get activeListings =>
      _listings.where((c) => c.status == 'active').toList();

  int get totalViews => _listings.fold<int>(0, (sum, c) => sum + c.views);
  int get totalBids => _listings.fold<int>(0, (sum, c) => sum + c.bidsCount);
  int get totalOrders => _listings.fold<int>(0, (sum, c) => sum + c.ordersCount);

  double get inventoryValue => _listings
      .where((c) => c.status == 'active')
      .fold<double>(0, (sum, c) => sum + c.currentPrice * c.quantityAvailable);

  void addListing({
    required String name,
    required String category,
    required String emoji,
    required double price,
    required int quantity,
    required String grade,
    required String location,
    required String farmerName,
    bool isOrganic = false,
  }) {
    _listings.insert(
      0,
      CropItem(
        id: 'lot-${DateTime.now().millisecondsSinceEpoch}',
        name: name,
        category: category,
        variety: grade,
        currentPrice: price,
        unit: 'Quintal',
        priceTrend: 0,
        expectedHarvestDate: 'Listed just now',
        daysToHarvest: 7,
        biddingActive: true,
        lastTwoDaysAIActive: false,
        quantityAvailable: quantity,
        location: location,
        farmerName: farmerName,
        emoji: emoji,
        status: 'pending_approval',
        grade: grade,
        isOrganic: isOrganic,
      ),
    );
    notifyListeners();
  }

  void updatePrice(String id, double price) {
    if (price <= 0) return;
    final index = _listings.indexWhere((c) => c.id == id);
    if (index == -1) return;
    _listings[index] = _listings[index].copyWith(currentPrice: price);
    notifyListeners();
  }

  void togglePause(String id) {
    final index = _listings.indexWhere((c) => c.id == id);
    if (index == -1) return;
    final current = _listings[index];
    _listings[index] = current.copyWith(
      status: current.status == 'paused' ? 'active' : 'paused',
    );
    notifyListeners();
  }

  void remove(String id) {
    _listings.removeWhere((c) => c.id == id);
    notifyListeners();
  }
}
