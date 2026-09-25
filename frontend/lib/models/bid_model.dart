class LiveBid {
  final String id;
  final String buyerName;
  final String companyName;
  final double amount;
  final String timestamp;
  final bool isHighest;
  final bool verifiedBuyer;

  const LiveBid({
    required this.id,
    required this.buyerName,
    required this.companyName,
    required this.amount,
    required this.timestamp,
    this.isHighest = false,
    this.verifiedBuyer = true,
  });

  LiveBid copyWith({
    String? id,
    String? buyerName,
    String? companyName,
    double? amount,
    String? timestamp,
    bool? isHighest,
    bool? verifiedBuyer,
  }) {
    return LiveBid(
      id: id ?? this.id,
      buyerName: buyerName ?? this.buyerName,
      companyName: companyName ?? this.companyName,
      amount: amount ?? this.amount,
      timestamp: timestamp ?? this.timestamp,
      isHighest: isHighest ?? this.isHighest,
      verifiedBuyer: verifiedBuyer ?? this.verifiedBuyer,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'buyerName': buyerName,
        'companyName': companyName,
        'amount': amount,
        'timestamp': timestamp,
        'isHighest': isHighest,
        'verifiedBuyer': verifiedBuyer,
      };

  factory LiveBid.fromJson(Map<String, dynamic> json) => LiveBid(
        id: json['id'] as String,
        buyerName: json['buyerName'] as String,
        companyName: json['companyName'] as String,
        amount: (json['amount'] as num).toDouble(),
        timestamp: json['timestamp'] as String,
        isHighest: json['isHighest'] as bool? ?? false,
        verifiedBuyer: json['verifiedBuyer'] as bool? ?? true,
      );
}
