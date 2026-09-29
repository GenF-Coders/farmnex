import 'package:flutter/material.dart';

class DeliveryTrip {
  final String id;
  final String orderId;
  final String cropName;
  final String emoji;
  final String pickup;
  final String drop;
  final double distanceKm;
  final double weightQuintal;
  final double payout;
  final String vehicleNeeded;
  final String status;
  final String otp;
  final String scheduledFor;

  const DeliveryTrip({
    required this.id,
    required this.orderId,
    required this.cropName,
    required this.emoji,
    required this.pickup,
    required this.drop,
    required this.distanceKm,
    required this.weightQuintal,
    required this.payout,
    required this.vehicleNeeded,
    required this.otp,
    this.status = 'available',
    this.scheduledFor = 'Today',
  });

  String get statusSymbol {
    switch (status) {
      case 'accepted':
        return '🤝';
      case 'picked':
        return '📦';
      case 'in_transit':
        return '🚚';
      case 'delivered':
        return '✅';
      default:
        return '🆕';
    }
  }

  bool get isOpen => status == 'available';
  bool get isDone => status == 'delivered';

  DeliveryTrip copyWith({String? status}) => DeliveryTrip(
        id: id,
        orderId: orderId,
        cropName: cropName,
        emoji: emoji,
        pickup: pickup,
        drop: drop,
        distanceKm: distanceKm,
        weightQuintal: weightQuintal,
        payout: payout,
        vehicleNeeded: vehicleNeeded,
        otp: otp,
        status: status ?? this.status,
        scheduledFor: scheduledFor,
      );
}

class LogisticsProvider extends ChangeNotifier {
  final List<DeliveryTrip> _trips = [
    const DeliveryTrip(
      id: 'trip-1',
      orderId: 'ord-8821',
      cropName: 'Sharbati Wheat',
      emoji: '🌾',
      pickup: 'Depalpur Village, Indore',
      drop: 'Kishanlal Agro Warehouse, Indore APMC',
      distanceKm: 42,
      weightQuintal: 100,
      payout: 4800,
      vehicleNeeded: '🚛 Truck (10T)',
      otp: '4417',
      scheduledFor: 'Today • 4:00 PM',
    ),
    const DeliveryTrip(
      id: 'trip-2',
      orderId: 'ord-8834',
      cropName: 'Yellow Soybean',
      emoji: '🌱',
      pickup: 'Ausa Road, Latur',
      drop: 'Adani Wilmar Plant, Pune',
      distanceKm: 386,
      weightQuintal: 50,
      payout: 11200,
      vehicleNeeded: '🚛 Truck (16T)',
      otp: '9032',
      scheduledFor: 'Tomorrow • 6:00 AM',
    ),
    const DeliveryTrip(
      id: 'trip-3',
      orderId: 'ord-8840',
      cropName: 'Nashik Onion',
      emoji: '🧅',
      pickup: 'Lasalgaon Mandi Yard',
      drop: 'Vashi APMC, Navi Mumbai',
      distanceKm: 198,
      weightQuintal: 80,
      payout: 7600,
      vehicleNeeded: '🚚 Tempo (7T)',
      otp: '6621',
      scheduledFor: 'Today • 9:00 PM',
    ),
    const DeliveryTrip(
      id: 'trip-4',
      orderId: 'ord-8712',
      cropName: 'Kolar Tomato',
      emoji: '🍅',
      pickup: 'Kolar Farm Cluster',
      drop: 'HOPCOMS Cold Store, Bengaluru',
      distanceKm: 71,
      weightQuintal: 30,
      payout: 3400,
      vehicleNeeded: '❄️ Reefer Van',
      otp: '1188',
      status: 'delivered',
      scheduledFor: 'Yesterday',
    ),
  ];

  String _vehicleStatus = 'online';

  List<DeliveryTrip> get trips => List.unmodifiable(_trips);

  List<DeliveryTrip> get availableTrips =>
      _trips.where((t) => t.status == 'available').toList();

  List<DeliveryTrip> get activeTrips => _trips
      .where((t) => t.status == 'accepted' || t.status == 'picked' || t.status == 'in_transit')
      .toList();

  List<DeliveryTrip> get completedTrips =>
      _trips.where((t) => t.status == 'delivered').toList();

  String get vehicleStatus => _vehicleStatus;
  bool get isOnline => _vehicleStatus == 'online';

  double get earningsPaid =>
      completedTrips.fold<double>(0, (sum, t) => sum + t.payout);

  double get earningsPending =>
      activeTrips.fold<double>(0, (sum, t) => sum + t.payout);

  double get kmCovered =>
      completedTrips.fold<double>(0, (sum, t) => sum + t.distanceKm);

  void toggleOnline() {
    _vehicleStatus = _vehicleStatus == 'online' ? 'offline' : 'online';
    notifyListeners();
  }

  void accept(String tripId) => _setStatus(tripId, 'accepted');

  void markPicked(String tripId) => _setStatus(tripId, 'picked');

  void startTransit(String tripId) => _setStatus(tripId, 'in_transit');

  bool confirmDelivery(String tripId, String enteredOtp) {
    final index = _trips.indexWhere((t) => t.id == tripId);
    if (index == -1) return false;
    if (_trips[index].otp != enteredOtp.trim()) return false;
    _trips[index] = _trips[index].copyWith(status: 'delivered');
    notifyListeners();
    return true;
  }

  void _setStatus(String tripId, String status) {
    final index = _trips.indexWhere((t) => t.id == tripId);
    if (index == -1) return;
    _trips[index] = _trips[index].copyWith(status: status);
    notifyListeners();
  }
}
