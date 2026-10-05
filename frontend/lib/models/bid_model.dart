/// Backend decimals arrive as JSON strings ("12.50") or numbers.
double _toDouble(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}

/// One row of `GET /api/v2/bid-events`: pre-bidding opened by a farmer on one of their lots.
class BidEventModel {
  final String publicId;
  final String listingId;
  final DateTime startsAt;
  final DateTime endsAt;
  final double startingPrice;
  final double minimumIncrement;
  final String status;
  final String? winnerBidId;

  const BidEventModel({
    required this.publicId,
    required this.listingId,
    required this.startsAt,
    required this.endsAt,
    required this.startingPrice,
    required this.minimumIncrement,
    required this.status,
    this.winnerBidId,
  });

  bool get isOpen => status == 'ACTIVE';

  factory BidEventModel.fromJson(Map<String, dynamic> json) => BidEventModel(
        publicId: json['public_id'].toString(),
        listingId: json['listing_id'].toString(),
        startsAt: DateTime.parse(json['starts_at'].toString()),
        endsAt: DateTime.parse(json['ends_at'].toString()),
        startingPrice: _toDouble(json['starting_price']),
        minimumIncrement: _toDouble(json['minimum_increment']),
        status: (json['status'] ?? '').toString(),
        winnerBidId: json['winner_bid_id']?.toString(),
      );
}

/// One row of `GET /api/v2/bids`. `amount` is the price per unit; `quantity` is what the buyer
/// commits to buy if the farmer accepts.
class BidModel {
  final String publicId;
  final String bidEventId;
  final String bidderId;
  final double amount;
  final double? quantity;
  final String status;
  final DateTime placedAt;

  const BidModel({
    required this.publicId,
    required this.bidEventId,
    required this.bidderId,
    required this.amount,
    this.quantity,
    required this.status,
    required this.placedAt,
  });

  bool get isActive => status == 'ACTIVE';
  bool get isWon => status == 'WON';
  bool get isLost => status == 'LOST';

  factory BidModel.fromJson(Map<String, dynamic> json) => BidModel(
        publicId: json['public_id'].toString(),
        bidEventId: json['bid_event_id'].toString(),
        bidderId: json['bidder_id'].toString(),
        amount: _toDouble(json['amount']),
        quantity: json['quantity'] == null ? null : _toDouble(json['quantity']),
        status: (json['status'] ?? '').toString(),
        placedAt: DateTime.parse(json['placed_at'].toString()),
      );
}

/// What the server returns when the farmer accepts a bid.
class BidAcceptResult {
  final BidEventModel event;
  final BidModel bid;
  final String? orderNumber;

  const BidAcceptResult({required this.event, required this.bid, this.orderNumber});

  factory BidAcceptResult.fromJson(Map<String, dynamic> json) => BidAcceptResult(
        event: BidEventModel.fromJson(json['bid_event'] as Map<String, dynamic>),
        bid: BidModel.fromJson(json['bid'] as Map<String, dynamic>),
        orderNumber: (json['order'] as Map<String, dynamic>?)?['order_number']?.toString(),
      );
}

/// "5 min ago" style text for a bid's time.
String bidTimeAgo(DateTime when) {
  final diff = DateTime.now().difference(when.toLocal());
  if (diff.inMinutes < 1) return 'Just now';
  if (diff.inMinutes < 60) return '${diff.inMinutes} min ago';
  if (diff.inHours < 24) return '${diff.inHours} h ago';
  return '${diff.inDays} d ago';
}
