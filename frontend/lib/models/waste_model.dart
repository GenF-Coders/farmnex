/// One waste lot for sale (`waste-utilization-listings`). Money and quantity are kept as numbers.
class WasteItem {
  final String id;
  final String title;
  final String utilizationType;
  final double quantity;
  final String unit;
  final double price;
  final String status;
  final DateTime createdAt;

  const WasteItem({
    required this.id,
    required this.title,
    required this.utilizationType,
    required this.quantity,
    required this.unit,
    required this.price,
    required this.status,
    required this.createdAt,
  });

  /// Price is per unit; the total is what the lot is worth.
  double get total => price * quantity;

  factory WasteItem.fromJson(Map<String, dynamic> json) => WasteItem(
        id: json['public_id'].toString(),
        title: (json['title'] ?? '').toString(),
        utilizationType: (json['utilization_type'] ?? '').toString(),
        quantity: double.tryParse(json['quantity'].toString()) ?? 0,
        unit: (json['unit'] ?? '').toString(),
        price: double.tryParse(json['price'].toString()) ?? 0,
        status: (json['status'] ?? '').toString(),
        createdAt: DateTime.tryParse((json['created_at'] ?? '').toString()) ?? DateTime.now(),
      );
}
