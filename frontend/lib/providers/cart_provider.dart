import 'package:flutter/material.dart';

import '../models/crop_model.dart';

class CartLine {
  final CropItem crop;
  final int quantity;

  const CartLine({required this.crop, required this.quantity});

  double get lineTotal => crop.currentPrice * quantity;

  CartLine copyWith({int? quantity}) =>
      CartLine(crop: crop, quantity: quantity ?? this.quantity);
}

class CartProvider extends ChangeNotifier {
  final List<CartLine> _lines = [];

  List<CartLine> get lines => List.unmodifiable(_lines);

  int get itemCount => _lines.length;

  int get totalQuantity =>
      _lines.fold<int>(0, (sum, line) => sum + line.quantity);

  double get subtotal =>
      _lines.fold<double>(0, (sum, line) => sum + line.lineTotal);

  bool get isEmpty => _lines.isEmpty;

  bool contains(String cropId) => _lines.any((l) => l.crop.id == cropId);

  void add(CropItem crop, {int quantity = 10}) {
    final index = _lines.indexWhere((l) => l.crop.id == crop.id);
    if (index == -1) {
      _lines.add(CartLine(crop: crop, quantity: quantity));
    } else {
      final merged = _lines[index].quantity + quantity;
      _lines[index] = _lines[index].copyWith(
        quantity: merged > crop.quantityAvailable ? crop.quantityAvailable : merged,
      );
    }
    notifyListeners();
  }

  void setQuantity(String cropId, int quantity) {
    final index = _lines.indexWhere((l) => l.crop.id == cropId);
    if (index == -1) return;
    if (quantity <= 0) {
      _lines.removeAt(index);
    } else {
      final max = _lines[index].crop.quantityAvailable;
      _lines[index] =
          _lines[index].copyWith(quantity: quantity > max ? max : quantity);
    }
    notifyListeners();
  }

  void remove(String cropId) {
    _lines.removeWhere((l) => l.crop.id == cropId);
    notifyListeners();
  }

  void clear() {
    _lines.clear();
    notifyListeners();
  }
}
