
class RescueListing {
  final String id;
  final String cropName;
  final String category;
  final String emoji;
  final double quantity;
  final String unit;
  final double pricePerUnit;
  final String location;
  final DateTime sellBy;
  final String description;
  final String imageUrl;
  final String farmerId;
  final String farmerName;
  final String status;
  final double soldQuantity;
  final int orderCount;
  final DateTime publishedAt;

  const RescueListing({
    required this.id,
    required this.cropName,
    required this.category,
    required this.emoji,
    required this.quantity,
    required this.unit,
    required this.pricePerUnit,
    required this.location,
    required this.sellBy,
    required this.farmerId,
    required this.farmerName,
    required this.publishedAt,
    this.description = '',
    this.imageUrl = '',
    this.status = 'active',
    this.soldQuantity = 0,
    this.orderCount = 0,
  });

  double get remainingQuantity {
    final left = quantity - soldQuantity;
    return left < 0 ? 0 : left;
  }

  double get totalValue => pricePerUnit * remainingQuantity;

  bool get isAvailable => status == 'active' && remainingQuantity > 0;

  int get daysLeft {
    final now = DateTime.now();
    final target = DateTime(sellBy.year, sellBy.month, sellBy.day);
    final today = DateTime(now.year, now.month, now.day);
    return target.difference(today).inDays;
  }

  String get urgencySymbol {
    if (daysLeft <= 1) return '🔴';
    if (daysLeft <= 3) return '🟠';
    return '🟢';
  }

  String get statusSymbol {
    switch (status) {
      case 'paused':
        return '⏸️';
      case 'sold_out':
        return '✅';
      default:
        return '🟢';
    }
  }

  RescueListing copyWith({
    String? cropName,
    double? quantity,
    double? pricePerUnit,
    String? status,
    double? soldQuantity,
    int? orderCount,
    DateTime? sellBy,
    String? description,
  }) {
    return RescueListing(
      id: id,
      cropName: cropName ?? this.cropName,
      category: category,
      emoji: emoji,
      quantity: quantity ?? this.quantity,
      unit: unit,
      pricePerUnit: pricePerUnit ?? this.pricePerUnit,
      location: location,
      sellBy: sellBy ?? this.sellBy,
      description: description ?? this.description,
      imageUrl: imageUrl,
      farmerId: farmerId,
      farmerName: farmerName,
      status: status ?? this.status,
      soldQuantity: soldQuantity ?? this.soldQuantity,
      orderCount: orderCount ?? this.orderCount,
      publishedAt: publishedAt,
    );
  }

  factory RescueListing.fromJson(Map<String, dynamic> json) {
    return RescueListing(
      id: json['id']?.toString() ?? '',
      cropName: json['crop_name'] ?? '',
      category: json['category'] ?? '',
      emoji: json['emoji'] ?? '🌾',
      quantity: (json['quantity'] ?? 0).toDouble(),
      unit: json['unit'] ?? 'kg',
      pricePerUnit: (json['price_per_unit'] ?? 0).toDouble(),
      location: json['location'] ?? '',
      sellBy: DateTime.tryParse(json['sell_by'] ?? '') ?? DateTime.now(),
      description: json['description'] ?? '',
      imageUrl: json['image_url'] ?? '',
      farmerId: json['farmer_id']?.toString() ?? '',
      farmerName: json['farmer_name'] ?? '',
      status: json['status'] ?? 'active',
      soldQuantity: (json['sold_quantity'] ?? 0).toDouble(),
      orderCount: json['order_count'] ?? 0,
      publishedAt: DateTime.tryParse(json['published_at'] ?? '') ?? DateTime.now(),
    );
  }

  Map<String, dynamic> toJson() => {
        'crop_name': cropName,
        'category': category,
        'emoji': emoji,
        'quantity': quantity,
        'unit': unit,
        'price_per_unit': pricePerUnit,
        'location': location,
        'sell_by': sellBy.toIso8601String(),
        'description': description,
        'image_url': imageUrl,
      };
}
