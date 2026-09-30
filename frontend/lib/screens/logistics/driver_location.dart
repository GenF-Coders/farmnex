import 'package:geolocator/geolocator.dart';

/// One place for the phone's GPS. Returns null when location is off or not allowed, so the
/// screens can show a short message instead of crashing. Only called while a driver screen is open.
Future<Position?> currentDriverPosition() async {
  try {
    if (!await Geolocator.isLocationServiceEnabled()) return null;
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) {
      permission = await Geolocator.requestPermission();
    }
    if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
      return null;
    }
    return await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(
        accuracy: LocationAccuracy.high,
        timeLimit: Duration(seconds: 15),
      ),
    );
  } catch (_) {
    return null;
  }
}
