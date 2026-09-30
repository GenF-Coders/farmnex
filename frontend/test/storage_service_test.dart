import 'package:farmnex_flutter/core/storage/storage_service.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('old plain-text tokens are moved to secure storage and deleted from shared_preferences', () async {
    FlutterSecureStorage.setMockInitialValues({});
    SharedPreferences.setMockInitialValues({
      'farmnex_access_token': 'old-access',
      'farmnex_refresh_token': 'old-refresh',
    });

    final storage = await StorageService.getInstance();

    expect(storage.getAccessToken(), 'old-access');
    expect(storage.getRefreshToken(), 'old-refresh');
    final prefs = await SharedPreferences.getInstance();
    expect(prefs.getString('farmnex_access_token'), isNull);
    expect(prefs.getString('farmnex_refresh_token'), isNull);

    await storage.clearTokens();
    expect(storage.getAccessToken(), isNull);
    expect(storage.getRefreshToken(), isNull);
  });
}
