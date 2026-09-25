class CropItem {
  final String id;
  final String name;
  final String category;
  final String variety;
  final double currentPrice;
  final String unit;
  final double priceTrend;
  final String expectedHarvestDate;
  final int daysToHarvest;
  final bool biddingActive;
  final bool lastTwoDaysAIActive;
  final double? expectedMinPrice;
  final double? expectedMaxPrice;
  final int? aiConfidence;
  final String aiDemand;
  final List<String> aiReasons;
  final int quantityAvailable;
  final String location;
  final String farmerName;
  final String emoji;
  final bool isPerishable;

  final String farmerId;
  final String status;
  final String grade;
  final bool isOrganic;
  final String description;
  final double minPrice;
  final int views;
  final int ordersCount;
  final int bidsCount;
  final double rating;
  final int ratingCount;

  const CropItem({
    required this.id,
    required this.name,
    required this.category,
    required this.variety,
    required this.currentPrice,
    required this.unit,
    required this.priceTrend,
    required this.expectedHarvestDate,
    required this.daysToHarvest,
    required this.biddingActive,
    required this.lastTwoDaysAIActive,
    this.expectedMinPrice,
    this.expectedMaxPrice,
    this.aiConfidence,
    this.aiDemand = 'Moderate',
    this.aiReasons = const [],
    required this.quantityAvailable,
    required this.location,
    required this.farmerName,
    required this.emoji,
    this.isPerishable = false,
    this.farmerId = 'farmer-0',
    this.status = 'active',
    this.grade = 'Grade A',
    this.isOrganic = false,
    this.description = '',
    this.minPrice = 0,
    this.views = 0,
    this.ordersCount = 0,
    this.bidsCount = 0,
    this.rating = 4.5,
    this.ratingCount = 0,
  });

  CropItem copyWith({
    String? id,
    String? name,
    String? category,
    String? variety,
    double? currentPrice,
    String? unit,
    double? priceTrend,
    String? expectedHarvestDate,
    int? daysToHarvest,
    bool? biddingActive,
    bool? lastTwoDaysAIActive,
    double? expectedMinPrice,
    double? expectedMaxPrice,
    int? aiConfidence,
    String? aiDemand,
    List<String>? aiReasons,
    int? quantityAvailable,
    String? location,
    String? farmerName,
    String? emoji,
    bool? isPerishable,
    String? farmerId,
    String? status,
    String? grade,
    bool? isOrganic,
    String? description,
    double? minPrice,
    int? views,
    int? ordersCount,
    int? bidsCount,
    double? rating,
    int? ratingCount,
  }) {
    return CropItem(
      id: id ?? this.id,
      name: name ?? this.name,
      category: category ?? this.category,
      variety: variety ?? this.variety,
      currentPrice: currentPrice ?? this.currentPrice,
      unit: unit ?? this.unit,
      priceTrend: priceTrend ?? this.priceTrend,
      expectedHarvestDate: expectedHarvestDate ?? this.expectedHarvestDate,
      daysToHarvest: daysToHarvest ?? this.daysToHarvest,
      biddingActive: biddingActive ?? this.biddingActive,
      lastTwoDaysAIActive: lastTwoDaysAIActive ?? this.lastTwoDaysAIActive,
      expectedMinPrice: expectedMinPrice ?? this.expectedMinPrice,
      expectedMaxPrice: expectedMaxPrice ?? this.expectedMaxPrice,
      aiConfidence: aiConfidence ?? this.aiConfidence,
      aiDemand: aiDemand ?? this.aiDemand,
      aiReasons: aiReasons ?? this.aiReasons,
      quantityAvailable: quantityAvailable ?? this.quantityAvailable,
      location: location ?? this.location,
      farmerName: farmerName ?? this.farmerName,
      emoji: emoji ?? this.emoji,
      isPerishable: isPerishable ?? this.isPerishable,
      farmerId: farmerId ?? this.farmerId,
      status: status ?? this.status,
      grade: grade ?? this.grade,
      isOrganic: isOrganic ?? this.isOrganic,
      description: description ?? this.description,
      minPrice: minPrice ?? this.minPrice,
      views: views ?? this.views,
      ordersCount: ordersCount ?? this.ordersCount,
      bidsCount: bidsCount ?? this.bidsCount,
      rating: rating ?? this.rating,
      ratingCount: ratingCount ?? this.ratingCount,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'category': category,
        'variety': variety,
        'currentPrice': currentPrice,
        'unit': unit,
        'priceTrend': priceTrend,
        'expectedHarvestDate': expectedHarvestDate,
        'daysToHarvest': daysToHarvest,
        'biddingActive': biddingActive,
        'lastTwoDaysAIActive': lastTwoDaysAIActive,
        'expectedMinPrice': expectedMinPrice,
        'expectedMaxPrice': expectedMaxPrice,
        'aiConfidence': aiConfidence,
        'aiDemand': aiDemand,
        'aiReasons': aiReasons,
        'quantityAvailable': quantityAvailable,
        'location': location,
        'farmerName': farmerName,
        'emoji': emoji,
        'isPerishable': isPerishable,
        'farmerId': farmerId,
        'status': status,
        'grade': grade,
        'isOrganic': isOrganic,
        'description': description,
        'minPrice': minPrice,
        'views': views,
        'ordersCount': ordersCount,
        'bidsCount': bidsCount,
        'rating': rating,
        'ratingCount': ratingCount,
      };

  factory CropItem.fromJson(Map<String, dynamic> json) => CropItem(
        id: json['id'] as String,
        name: json['name'] as String,
        category: json['category'] as String,
        variety: json['variety'] as String,
        currentPrice: (json['currentPrice'] as num).toDouble(),
        unit: json['unit'] as String,
        priceTrend: (json['priceTrend'] as num).toDouble(),
        expectedHarvestDate: json['expectedHarvestDate'] as String,
        daysToHarvest: json['daysToHarvest'] as int,
        biddingActive: json['biddingActive'] as bool,
        lastTwoDaysAIActive: json['lastTwoDaysAIActive'] as bool,
        expectedMinPrice: (json['expectedMinPrice'] as num?)?.toDouble(),
        expectedMaxPrice: (json['expectedMaxPrice'] as num?)?.toDouble(),
        aiConfidence: json['aiConfidence'] as int?,
        aiDemand: json['aiDemand'] as String? ?? 'Moderate',
        aiReasons: (json['aiReasons'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
        quantityAvailable: json['quantityAvailable'] as int,
        location: json['location'] as String,
        farmerName: json['farmerName'] as String,
        emoji: json['emoji'] as String? ?? json['image'] as String? ?? '🌾',
        isPerishable: json['isPerishable'] as bool? ?? false,
        farmerId: json['farmerId'] as String? ?? 'farmer-0',
        status: json['status'] as String? ?? 'active',
        grade: json['grade'] as String? ?? 'Grade A',
        isOrganic: json['isOrganic'] as bool? ?? false,
        description: json['description'] as String? ?? '',
        minPrice: (json['minPrice'] as num?)?.toDouble() ?? 0,
        views: json['views'] as int? ?? 0,
        ordersCount: json['ordersCount'] as int? ?? 0,
        bidsCount: json['bidsCount'] as int? ?? 0,
        rating: (json['rating'] as num?)?.toDouble() ?? 4.5,
        ratingCount: json['ratingCount'] as int? ?? 0,
      );
}
