import 'crop_model.dart';

/// Backend decimals arrive as JSON strings ("12.50") or numbers.
double _toDouble(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}

/// Emoji + market category for a crop, found from its name (the listing reply has no crop type).
/// Names match the backend's crop types (`crop_types.name`).
const List<(String, String, String)> _cropLooks = [
  ('tomato', '🍅', 'Vegetables'),
  ('potato', '🥔', 'Vegetables'),
  ('onion', '🧅', 'Vegetables'),
  ('carrot', '🥕', 'Vegetables'),
  ('spinach', '🥬', 'Vegetables'),
  ('okra', '🫛', 'Vegetables'),
  ('brinjal', '🍆', 'Vegetables'),
  ('cauliflower', '🥦', 'Vegetables'),
  ('capsicum', '🫑', 'Vegetables'),
  ('cucumber', '🥒', 'Vegetables'),
  ('rice', '🌾', 'Grains'),
  ('wheat', '🌾', 'Grains'),
  ('maize', '🌽', 'Grains'),
  ('groundnut', '🥜', 'Oilseeds'),
  ('mango', '🥭', 'Fruits'),
  ('banana', '🍌', 'Fruits'),
  ('grapes', '🍇', 'Fruits'),
  ('cotton', '🌿', 'Other'),
  ('sugarcane', '🎋', 'Other'),
];

String cropEmojiFor(String name) {
  final lower = name.toLowerCase();
  for (final (key, emoji, _) in _cropLooks) {
    if (lower.contains(key)) return emoji;
  }
  return '🌱';
}

String cropCategoryFor(String name) {
  final lower = name.toLowerCase();
  for (final (key, _, category) in _cropLooks) {
    if (lower.contains(key)) return category;
  }
  return 'Other';
}

/// One row of `GET /api/v2/product-listings`.
class ListingModel {
  final String publicId;
  final String sellerId;
  final String farmId;
  final String cropBatchId;
  final String title;
  final String? description;
  final String listingType;
  final double price;
  final String currency;
  final double quantity;
  final double availableQuantity;
  final String unit;
  final String status;

  /// Only on the reply to "create": the Crop Rescue spoilage timer started for this lot,
  /// or a short reason why none was started.
  final String? rescueLotId;
  final String? rescueNote;

  /// From GET: "Verified by FarmNex" status (NONE / PENDING / VERIFIED / REJECTED) and photo/video count.
  final String verificationStatus;
  final int mediaCount;

  const ListingModel({
    required this.publicId,
    required this.sellerId,
    required this.farmId,
    required this.cropBatchId,
    required this.title,
    this.description,
    required this.listingType,
    required this.price,
    required this.currency,
    required this.quantity,
    required this.availableQuantity,
    required this.unit,
    required this.status,
    this.rescueLotId,
    this.rescueNote,
    this.verificationStatus = 'NONE',
    this.mediaCount = 0,
  });

  factory ListingModel.fromJson(Map<String, dynamic> json) => ListingModel(
        publicId: json['public_id'].toString(),
        sellerId: json['seller_id'].toString(),
        farmId: json['farm_id'].toString(),
        cropBatchId: json['crop_batch_id'].toString(),
        title: (json['title'] ?? '').toString(),
        description: json['description'] as String?,
        listingType: (json['listing_type'] ?? '').toString(),
        price: _toDouble(json['price']),
        currency: (json['currency'] ?? 'INR').toString(),
        quantity: _toDouble(json['quantity']),
        availableQuantity: _toDouble(json['available_quantity']),
        unit: (json['unit'] ?? '').toString(),
        status: (json['status'] ?? '').toString(),
        rescueLotId: json['rescue_lot_id'] as String?,
        rescueNote: json['rescue_note'] as String?,
        verificationStatus: (json['verification_status'] ?? 'NONE').toString(),
        mediaCount: (json['media_count'] as num?)?.toInt() ?? 0,
      );

  /// The shape the existing screens already use. Fields the backend doesn't have yet
  /// (views, ratings, farmer name, location, AI numbers) stay empty or zero.
  CropItem toCropItem() => CropItem(
        id: publicId,
        name: title,
        category: cropCategoryFor(title),
        variety: description ?? '',
        currentPrice: price,
        unit: unit,
        priceTrend: 0,
        expectedHarvestDate: '',
        daysToHarvest: 0,
        biddingActive: listingType == 'PRE_BID',
        lastTwoDaysAIActive: false,
        quantityAvailable: availableQuantity.floor(),
        location: '',
        farmerName: '',
        emoji: cropEmojiFor(title),
        farmerId: sellerId,
        status: status.toLowerCase(),
        grade: '',
        description: description ?? '',
        rating: 0,
        verificationStatus: verificationStatus,
      );
}

/// One row of `GET /api/v2/crop-types`.
class CropTypeModel {
  final String publicId;
  final String name;
  final String? category;
  final String defaultUnit;

  const CropTypeModel({required this.publicId, required this.name, this.category, required this.defaultUnit});

  String get emoji => cropEmojiFor(name);

  factory CropTypeModel.fromJson(Map<String, dynamic> json) => CropTypeModel(
        publicId: json['public_id'].toString(),
        name: (json['name'] ?? '').toString(),
        category: json['category'] as String?,
        defaultUnit: (json['default_unit'] ?? 'kg').toString(),
      );
}

/// The few farm fields the lot form needs (`GET /api/v2/farms` → items).
class FarmSummary {
  final String publicId;
  final String farmName;
  final String? city;
  final String? district;

  const FarmSummary({required this.publicId, required this.farmName, this.city, this.district});

  factory FarmSummary.fromJson(Map<String, dynamic> json) => FarmSummary(
        publicId: json['public_id'].toString(),
        farmName: (json['farm_name'] ?? '').toString(),
        city: json['city'] as String?,
        district: json['district'] as String?,
      );
}
