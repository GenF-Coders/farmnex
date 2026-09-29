class WasteItem {
  final String id;
  final String farmerName;
  final String wasteType;
  final String quantity;
  final String location;
  final String bestUse;
  final String potentialIncome;
  final String createdDate;

  const WasteItem({
    required this.id,
    required this.farmerName,
    required this.wasteType,
    required this.quantity,
    required this.location,
    required this.bestUse,
    required this.potentialIncome,
    required this.createdDate,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'farmerName': farmerName,
        'wasteType': wasteType,
        'quantity': quantity,
        'location': location,
        'bestUse': bestUse,
        'potentialIncome': potentialIncome,
        'createdDate': createdDate,
      };

  factory WasteItem.fromJson(Map<String, dynamic> json) => WasteItem(
        id: json['id'] as String,
        farmerName: json['farmerName'] as String,
        wasteType: json['wasteType'] as String,
        quantity: json['quantity'] as String,
        location: json['location'] as String,
        bestUse: json['bestUse'] as String,
        potentialIncome: json['potentialIncome'] as String,
        createdDate: json['createdDate'] as String,
      );
}
