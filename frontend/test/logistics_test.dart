import 'package:flutter_test/flutter_test.dart';
import 'package:farmnex_flutter/core/network/route_api.dart';
import 'package:farmnex_flutter/models/user_model.dart';

void main() {
  test('driver sign-up sends DELIVERY_AGENT and the backend roles map to logistics', () {
    expect(UserRole.logistics.apiValue, 'DELIVERY_AGENT');
    expect(UserRole.fromString('DELIVERY_AGENT'), UserRole.logistics);
    expect(UserRole.fromString('LOGISTICS_MANAGER'), UserRole.logistics);
    expect(UserRole.fromString('logistics'), UserRole.logistics); // saved sessions
  });

  test('trip and delivery models read the backend JSON', () {
    final trip = TripModel.fromJson({
      'id': 't1',
      'status': 'in_progress',
      'is_backhaul': false,
      'total_distance_km': 12.5,
      'total_duration_min': 30,
      'estimated_cost': 900,
      'stops': [
        {'id': 's2', 'seq': 2, 'kind': 'drop', 'load_id': 'l1', 'label': 'B', 'status': 'pending'},
        {'id': 's1', 'seq': 1, 'kind': 'pickup', 'load_id': 'l1', 'label': 'A', 'status': 'done'},
      ],
    });
    expect(trip.isRunning, isTrue);
    expect(trip.nextStop!.id, 's2');

    final d = OrderDelivery.fromJson({
      'status': 'assigned',
      'tracking_url': 'https://x/track/1/view?load=l1',
      'vehicle': {'vehicle_number': 'MH12AB1234'},
      'delivery': {'eta_min': 42.5},
    });
    expect(d.canTrack, isTrue);
    expect(d.etaMin, 42.5);
  });
}
