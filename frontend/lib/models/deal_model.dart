class CropDeal {
  final String id;
  final String cropId;
  final String cropName;
  final String cropEmoji;
  final String buyerName;
  final String buyerCompany;
  final String buyerLocation;
  final bool buyerVerified;
  final double bidPrice;
  final double quantity;
  final String unit;
  final double totalAmount;
  final String harvestDate;
  final String status;
  final double? counterPrice;
  final String timestamp;

  const CropDeal({
    required this.id,
    required this.cropId,
    required this.cropName,
    required this.cropEmoji,
    required this.buyerName,
    required this.buyerCompany,
    required this.buyerLocation,
    this.buyerVerified = true,
    required this.bidPrice,
    required this.quantity,
    required this.unit,
    required this.totalAmount,
    required this.harvestDate,
    required this.status,
    this.counterPrice,
    required this.timestamp,
  });

  CropDeal copyWith({
    String? status,
    double? counterPrice,
  }) {
    return CropDeal(
      id: id,
      cropId: cropId,
      cropName: cropName,
      cropEmoji: cropEmoji,
      buyerName: buyerName,
      buyerCompany: buyerCompany,
      buyerLocation: buyerLocation,
      buyerVerified: buyerVerified,
      bidPrice: bidPrice,
      quantity: quantity,
      unit: unit,
      totalAmount: totalAmount,
      harvestDate: harvestDate,
      status: status ?? this.status,
      counterPrice: counterPrice ?? this.counterPrice,
      timestamp: timestamp,
    );
  }
}

class SaleRecord {
  final String id;
  final String cropName;
  final String variety;
  final double quantity;
  final String unit;
  final double pricePerUnit;
  final double totalIncome;
  final String buyerName;
  final String buyerCompany;
  final String mandi;
  final String saleDate;
  final String payoutStatus;
  final String receiptNo;

  const SaleRecord({
    required this.id,
    required this.cropName,
    required this.variety,
    required this.quantity,
    required this.unit,
    required this.pricePerUnit,
    required this.totalIncome,
    required this.buyerName,
    required this.buyerCompany,
    required this.mandi,
    required this.saleDate,
    required this.payoutStatus,
    required this.receiptNo,
  });
}

class CropMediaItem {
  final String id;
  final String type;
  final String url;
  final String title;
  final String fileSize;
  final String? duration;
  final String uploadDate;
  final String verifiedStatus;

  const CropMediaItem({
    required this.id,
    required this.type,
    required this.url,
    required this.title,
    required this.fileSize,
    this.duration,
    required this.uploadDate,
    required this.verifiedStatus,
  });
}

class FarmerCropSetting {
  final String id;
  final String cropId;
  final String cropName;
  final String variety;
  final double currentMandiPrice;
  final double minReservePrice;
  final double expectedMaxPrice;
  final String harvestDate;
  final bool biddingEnabled;
  final bool isRescueListed;
  final double? rescuePrice;
  final String? wasteResidueType;
  final String? wasteQuantity;
  final double? wasteTargetPrice;
  final bool isWasteListed;
  final List<CropMediaItem> media;

  const FarmerCropSetting({
    required this.id,
    required this.cropId,
    required this.cropName,
    required this.variety,
    required this.currentMandiPrice,
    required this.minReservePrice,
    required this.expectedMaxPrice,
    required this.harvestDate,
    required this.biddingEnabled,
    this.isRescueListed = false,
    this.rescuePrice,
    this.wasteResidueType,
    this.wasteQuantity,
    this.wasteTargetPrice,
    this.isWasteListed = false,
    this.media = const [],
  });

  FarmerCropSetting copyWith({
    bool? biddingEnabled,
    bool? isRescueListed,
    double? rescuePrice,
    bool? isWasteListed,
    List<CropMediaItem>? media,
  }) {
    return FarmerCropSetting(
      id: id,
      cropId: cropId,
      cropName: cropName,
      variety: variety,
      currentMandiPrice: currentMandiPrice,
      minReservePrice: minReservePrice,
      expectedMaxPrice: expectedMaxPrice,
      harvestDate: harvestDate,
      biddingEnabled: biddingEnabled ?? this.biddingEnabled,
      isRescueListed: isRescueListed ?? this.isRescueListed,
      rescuePrice: rescuePrice ?? this.rescuePrice,
      wasteResidueType: wasteResidueType,
      wasteQuantity: wasteQuantity,
      wasteTargetPrice: wasteTargetPrice,
      isWasteListed: isWasteListed ?? this.isWasteListed,
      media: media ?? this.media,
    );
  }
}
