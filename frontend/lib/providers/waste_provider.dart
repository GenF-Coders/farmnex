import 'package:flutter/material.dart';
import '../models/waste_model.dart';

class WasteProvider extends ChangeNotifier {
  final List<WasteItem> _items = [];
  bool _isListing = false;

  List<WasteItem> get items => _items;
  bool get isListing => _isListing;

  WasteProvider() {
    _initDefaultItems();
  }

  void _initDefaultItems() {
    _items.addAll([
      const WasteItem(
        id: 'w-1',
        farmerName: 'Balasaheb Shinde',
        wasteType: 'Paddy Straw (धान की पराली)',
        quantity: '12 Tonnes',
        location: 'Latur, Maharashtra',
        bestUse: 'Bio-CNG & Thermal Pellets',
        potentialIncome: '₹16,800 (@ ₹1,400/T)',
        createdDate: 'Yesterday',
      ),
      const WasteItem(
        id: 'w-2',
        farmerName: 'Ramesh Patil',
        wasteType: 'Sugarcane Bagasse (गन्ने की खोई)',
        quantity: '25 Tonnes',
        location: 'Indore Mandi Region, MP',
        bestUse: 'Packaging Paper & Pulp',
        potentialIncome: '₹37,500 (@ ₹1,500/T)',
        createdDate: '2 Days ago',
      ),
      const WasteItem(
        id: 'w-3',
        farmerName: 'Sanjay Jadhav',
        wasteType: 'Corn Stalks (मक्के के डंठल)',
        quantity: '8 Tonnes',
        location: 'Nashik, Maharashtra',
        bestUse: 'Compressed Animal Fodder Pellets',
        potentialIncome: '₹9,600 (@ ₹1,200/T)',
        createdDate: '3 Days ago',
      ),
    ]);
  }

  Future<bool> createWasteListing({
    required String farmerName,
    required String wasteType,
    required String quantity,
    required String location,
    required String bestUse,
    required String potentialIncome,
    String? mediaPath,
  }) async {
    _isListing = true;
    notifyListeners();

    try {

      await Future.delayed(const Duration(milliseconds: 700));

      final newItem = WasteItem(
        id: 'w-${DateTime.now().millisecondsSinceEpoch}',
        farmerName: farmerName,
        wasteType: wasteType,
        quantity: quantity,
        location: location,
        bestUse: bestUse,
        potentialIncome: potentialIncome,
        createdDate: 'Just now',
      );

      _items.insert(0, newItem);
      _isListing = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isListing = false;
      notifyListeners();
      return false;
    }
  }
}
