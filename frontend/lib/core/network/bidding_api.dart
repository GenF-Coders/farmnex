import 'package:dio/dio.dart';

import '../../models/bid_model.dart';
import '../config/api_config.dart';
import 'api_client.dart';
import 'listing_api.dart' show listingErrorMessage;

/// Pre-bidding: events on a lot, bids on an event, and the farmer accepting a bid.
/// Identity comes from the login token; status, winner and order are set by the server.
class BiddingApi {
  final Dio _dio = ApiClient().dio;

  /// Events I can see (open ones from any farmer, plus my own).
  Future<List<BidEventModel>> listEvents({bool mine = false}) async {
    final response = await _dio.get<dynamic>(
      ApiConfig.bidEventsEndpoint,
      queryParameters: {'limit': 100, 'mine': ?(mine ? true : null)},
    );
    return (response.data as List<dynamic>).map((e) => BidEventModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<BidEventModel> openEvent({
    required String listingId,
    required DateTime startsAt,
    required DateTime endsAt,
    required double startingPrice,
    required double minimumIncrement,
  }) async {
    final response = await _dio.post<dynamic>(ApiConfig.bidEventsEndpoint, data: {
      'listing_id': listingId,
      'starts_at': startsAt.toUtc().toIso8601String(),
      'ends_at': endsAt.toUtc().toIso8601String(),
      'starting_price': startingPrice.toStringAsFixed(2),
      'minimum_increment': minimumIncrement.toStringAsFixed(2),
    });
    return BidEventModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// My own bids, plus the bids on events I opened (optionally only one event's).
  Future<List<BidModel>> listBids({String? eventId}) async {
    final response = await _dio.get<dynamic>(
      ApiConfig.bidsEndpoint,
      queryParameters: {'limit': 100, 'bid_event_id': ?eventId},
    );
    return (response.data as List<dynamic>).map((e) => BidModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<BidModel> placeBid({required String eventId, required double amount, required double quantity}) async {
    final response = await _dio.post<dynamic>(ApiConfig.bidsEndpoint, data: {
      'bid_event_id': eventId,
      'amount': amount.toStringAsFixed(2),
      'quantity': quantity.toStringAsFixed(3),
    });
    return BidModel.fromJson(response.data as Map<String, dynamic>);
  }

  /// Sending the same key again returns the same result, so a double tap can't accept twice.
  Future<BidAcceptResult> accept(String bidId, {required String idempotencyKey}) async {
    final response = await _dio.post<dynamic>(
      ApiConfig.bidAcceptEndpoint(bidId),
      options: Options(headers: {'Idempotency-Key': idempotencyKey}),
    );
    return BidAcceptResult.fromJson(response.data as Map<String, dynamic>);
  }
}

String biddingErrorMessage(Object error) => listingErrorMessage(error);
