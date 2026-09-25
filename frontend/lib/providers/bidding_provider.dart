import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import '../models/bid_model.dart';
import '../core/network/websocket_service.dart';

class BiddingProvider extends ChangeNotifier {
  final Map<String, List<LiveBid>> _bidsByCrop = {};
  final WebSocketService _wsService = WebSocketService();
  Timer? _simulationTimer;
  String? _activeCropId;

  Map<String, List<LiveBid>> get bidsByCrop => _bidsByCrop;

  BiddingProvider() {
    _initDefaultBids();
  }

  void _initDefaultBids() {
    _bidsByCrop['crop-1'] = [
      const LiveBid(
        id: 'bid-1',
        companyName: 'Kishanlal Agro Export',
        buyerName: 'Manoj Agarwal',
        amount: 2510,
        timestamp: '1 min ago',
        isHighest: true,
        verifiedBuyer: true,
      ),
      const LiveBid(
        id: 'bid-2',
        companyName: 'Godrej Agrovet Logistics',
        buyerName: 'Sunil Rao',
        amount: 2490,
        timestamp: '3 mins ago',
        isHighest: false,
        verifiedBuyer: true,
      ),
      const LiveBid(
        id: 'bid-3',
        companyName: 'South India Millers Co',
        buyerName: 'K. Venkatesan',
        amount: 2470,
        timestamp: '12 mins ago',
        isHighest: false,
        verifiedBuyer: true,
      ),
    ];

    _bidsByCrop['crop-2'] = [
      const LiveBid(
        id: 'bid-201',
        companyName: 'Adani Wilmar Refineries',
        buyerName: 'Prakash Deshmukh',
        amount: 4920,
        timestamp: '2 mins ago',
        isHighest: true,
        verifiedBuyer: true,
      ),
      const LiveBid(
        id: 'bid-202',
        companyName: 'Ruchi Soya Traders',
        buyerName: 'Nitin Kadam',
        amount: 4880,
        timestamp: '8 mins ago',
        isHighest: false,
        verifiedBuyer: true,
      ),
    ];
  }

  List<LiveBid> getBidsForCrop(String cropId) {
    return _bidsByCrop[cropId] ?? [];
  }

  double getHighestBid(String cropId, double defaultPrice) {
    final list = _bidsByCrop[cropId];
    if (list != null && list.isNotEmpty) {
      return list.first.amount;
    }
    return defaultPrice;
  }

  void startListeningToBids(String cropId) {
    _activeCropId = cropId;

    _wsService.connectToCropBids(cropId).listen((data) {
      try {
        final newBid = LiveBid.fromJson(data);
        _addIncomingBid(cropId, newBid);
      } catch (_) {}
    });

    _simulationTimer?.cancel();
    _simulationTimer = Timer.periodic(const Duration(seconds: 10), (_) {
      if (_activeCropId == cropId) {
        _simulateIncomingBid(cropId);
      }
    });
  }

  void stopListeningToBids() {
    _simulationTimer?.cancel();
    _simulationTimer = null;
    _activeCropId = null;
  }

  void _simulateIncomingBid(String cropId) {
    final currentBids = _bidsByCrop[cropId] ?? [];
    final currentTop = currentBids.isNotEmpty ? currentBids.first.amount : 2450.0;
    final increment = (Random().nextInt(25) + 15).toDouble();
    final newTop = currentTop + increment;

    final buyers = [
      {'name': 'Kishanlal Agro Export', 'buyer': 'Manoj Agarwal'},
      {'name': 'Godrej Agrovet Logistics', 'buyer': 'Sunil Rao'},
      {'name': 'ITC Choupal Sagar', 'buyer': 'Anand Mishra'},
      {'name': 'South India Millers Co', 'buyer': 'K. Venkatesan'},
    ];
    final chosen = buyers[Random().nextInt(buyers.length)];

    final newBid = LiveBid(
      id: 'sim-${DateTime.now().millisecondsSinceEpoch}',
      companyName: chosen['name']!,
      buyerName: chosen['buyer']!,
      amount: newTop,
      timestamp: 'Just now',
      isHighest: true,
      verifiedBuyer: true,
    );

    _addIncomingBid(cropId, newBid);
  }

  void _addIncomingBid(String cropId, LiveBid newBid) {
    final currentBids = _bidsByCrop[cropId] ?? [];
    final updated = [
      newBid,
      ...currentBids.map((b) => b.copyWith(isHighest: false)).take(5),
    ];
    _bidsByCrop[cropId] = updated;
    notifyListeners();
  }

  void placeBid({
    required String cropId,
    required String buyerName,
    required String companyName,
    required double amount,
  }) {
    final newBid = LiveBid(
      id: 'my-bid-${DateTime.now().millisecondsSinceEpoch}',
      companyName: companyName,
      buyerName: '$buyerName (You)',
      amount: amount,
      timestamp: 'Just now',
      isHighest: true,
      verifiedBuyer: true,
    );

    _addIncomingBid(cropId, newBid);

    _wsService.sendBid({
      'crop_id': cropId,
      'buyer_name': buyerName,
      'company_name': companyName,
      'amount': amount,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  Future<Map<String, dynamic>> fetchLastTwoDaysPricePrediction(String cropId) async {
    await Future.delayed(const Duration(milliseconds: 300));
    return {
      'crop_id': cropId,
      'current_price': 2450.0,
      'expected_max_price': 2550.0,
      'confidence': 86,
      'reasons': [
        'South India flour mill procurement spike',
        'Recent mandi arrivals 18% lower than 5-year average',
        'Export quote surge in port hubs over the past 48 hours',
      ],
    };
  }

  @override
  void dispose() {
    _simulationTimer?.cancel();
    _wsService.disconnect();
    super.dispose();
  }
}
