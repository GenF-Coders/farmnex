import 'package:flutter/material.dart';

import '../core/network/bidding_api.dart';
import '../models/bid_model.dart';

/// Pre-bidding on the real backend. A crop's id on screen is its listing's public id.
class BiddingProvider extends ChangeNotifier {
  final BiddingApi _api = BiddingApi();

  List<BidEventModel> _events = [];
  List<BidModel> _bids = [];
  bool _isLoading = false;
  bool _isBusy = false;
  String? _error;

  List<BidEventModel> get events => List.unmodifiable(_events);
  List<BidModel> get bids => List.unmodifiable(_bids);
  bool get isLoading => _isLoading;
  bool get isBusy => _isBusy;
  String? get error => _error;

  /// The event that is open for this lot, if any (the server allows only one at a time).
  BidEventModel? openEventForListing(String listingId) {
    for (final e in _events) {
      if (e.listingId == listingId && e.isOpen) return e;
    }
    return null;
  }

  BidEventModel? eventById(String eventId) {
    for (final e in _events) {
      if (e.publicId == eventId) return e;
    }
    return null;
  }

  /// Bids on one event, highest first (a buyer sees only their own; the event's farmer sees all).
  List<BidModel> bidsForEvent(String eventId) {
    final list = _bids.where((b) => b.bidEventId == eventId).toList();
    list.sort((a, b) => b.amount.compareTo(a.amount));
    return list;
  }

  double? highestBid(String eventId) {
    final list = bidsForEvent(eventId);
    return list.isEmpty ? null : list.first.amount;
  }

  Future<void> load() async {
    _isLoading = true;
    _error = null;
    notifyListeners();
    try {
      final results = await Future.wait([_api.listEvents(), _api.listBids()]);
      _events = results[0] as List<BidEventModel>;
      _bids = results[1] as List<BidModel>;
    } catch (e) {
      _error = biddingErrorMessage(e);
    }
    _isLoading = false;
    notifyListeners();
  }

  /// Forget everything (another person logged in).
  void clear() {
    _events = [];
    _bids = [];
    _error = null;
    notifyListeners();
  }

  /// Runs one write, then reloads. Returns null on success, or a short message for the screen.
  Future<String?> _write(Future<void> Function() action) async {
    _isBusy = true;
    notifyListeners();
    String? message;
    try {
      await action();
    } catch (e) {
      message = biddingErrorMessage(e);
    }
    _isBusy = false;
    notifyListeners();
    if (message == null) await load();
    return message;
  }

  Future<String?> openEvent({
    required String listingId,
    required double startingPrice,
    required double minimumIncrement,
    required Duration duration,
  }) {
    final now = DateTime.now();
    return _write(() => _api.openEvent(
          listingId: listingId,
          // A minute in the past so the server's clock never sees the start as "in the future".
          startsAt: now.subtract(const Duration(minutes: 1)),
          endsAt: now.add(duration),
          startingPrice: startingPrice,
          minimumIncrement: minimumIncrement,
        ));
  }

  Future<String?> placeBid({required String eventId, required double amount, required double quantity}) =>
      _write(() => _api.placeBid(eventId: eventId, amount: amount, quantity: quantity));

  /// Farmer accepts a bid. On success [onAccepted] gets the new order's number.
  Future<String?> acceptBid(String bidId, {void Function(String? orderNumber)? onAccepted}) {
    // One key per bid: repeating the tap returns the same result instead of a second order.
    return _write(() async {
      final result = await _api.accept(bidId, idempotencyKey: 'accept-$bidId');
      onAccepted?.call(result.orderNumber);
    });
  }
}
