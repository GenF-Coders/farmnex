class BuyerBidItem {
  final String id;
  final String cropId;
  final String cropName;
  final String cropImage;
  final String farmerName;
  final String mandiLocation;
  final double myBidPrice;
  final double highestBidPrice;
  final double quantity;
  final String unit;
  final String status;
  final String harvestDate;
  final String timestamp;

  const BuyerBidItem({
    required this.id,
    required this.cropId,
    required this.cropName,
    required this.cropImage,
    required this.farmerName,
    required this.mandiLocation,
    required this.myBidPrice,
    required this.highestBidPrice,
    required this.quantity,
    required this.unit,
    required this.status,
    required this.harvestDate,
    required this.timestamp,
  });

  BuyerBidItem copyWith({
    double? myBidPrice,
    double? highestBidPrice,
    String? status,
  }) {
    return BuyerBidItem(
      id: id,
      cropId: cropId,
      cropName: cropName,
      cropImage: cropImage,
      farmerName: farmerName,
      mandiLocation: mandiLocation,
      myBidPrice: myBidPrice ?? this.myBidPrice,
      highestBidPrice: highestBidPrice ?? this.highestBidPrice,
      quantity: quantity,
      unit: unit,
      status: status ?? this.status,
      harvestDate: harvestDate,
      timestamp: timestamp,
    );
  }
}

class BuyerPurchaseItem {
  final String id;
  final String cropName;
  final String cropImage;
  final String farmerName;
  final double quantity;
  final String unit;
  final double agreedPrice;
  final double totalAmount;
  final String escrowStatus;
  final String deliveryDate;
  final String transporterName;
  final String trackingId;

  const BuyerPurchaseItem({
    required this.id,
    required this.cropName,
    required this.cropImage,
    required this.farmerName,
    required this.quantity,
    required this.unit,
    required this.agreedPrice,
    required this.totalAmount,
    required this.escrowStatus,
    required this.deliveryDate,
    required this.transporterName,
    required this.trackingId,
  });
}
