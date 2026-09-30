
class ApiConfig {
  static const String baseUrl = 'https://farmnex-a.fastapicloud.dev';
  static const String wsBaseUrl = 'wss://farmnex-a.fastapicloud.dev';

  static const String healthEndpoint = '/health';
  static const String databaseHealthEndpoint = '/db';
  static const String readinessEndpoint = '/ready';

  static const String registerRequestOtpEndpoint = '/api/v2/auth/register/request-otp';
  static const String registerResendOtpEndpoint = '/api/v2/auth/register/resend';
  static const String registerVerifyOtpEndpoint = '/api/v2/auth/register/verify';
  static const String registerCompleteEndpoint = '/api/v2/auth/register/complete';
  static const String loginRequestOtpEndpoint = '/api/v2/auth/login/request-otp';
  static const String loginResendOtpEndpoint = '/api/v2/auth/login/resend';
  static const String loginVerifyOtpEndpoint = '/api/v2/auth/login/verify';
  static const String refreshTokenEndpoint = '/api/v2/auth/refresh';
  static const String logoutEndpoint = '/api/v2/auth/logout';

  static const String usersEndpoint = '/api/v2/users';
  static const String myProfileEndpoint = '/api/v2/users/me';
  static const String myProfileImageEndpoint = '/api/v2/users/me/image';
  static String userEndpoint(String publicId) => '$usersEndpoint/$publicId';

  static const String addressesEndpoint = '/api/v2/addresses';
  static String addressEndpoint(String publicId) => '$addressesEndpoint/$publicId';
  static String defaultAddressEndpoint(String publicId) => '${addressEndpoint(publicId)}/default';
  static String deactivateAddressEndpoint(String publicId) => '${addressEndpoint(publicId)}/deactivate';
  static String activateAddressEndpoint(String publicId) => '${addressEndpoint(publicId)}/activate';

  static const String farmsEndpoint = '/api/v2/farms';
  static String farmEndpoint(String publicId) => '$farmsEndpoint/$publicId';
  static String farmFileEndpoint(String publicId) => '${farmEndpoint(publicId)}/file';
  static String farmFileDownloadEndpoint(String publicId) => '${farmFileEndpoint(publicId)}/download';

  static const String verificationUploadEndpoint = '/api/verification/upload';
  static const String aiChatEndpoint = '/api/ai/chat';

  // Old URLs below do not exist on the backend yet. Each sits in the section of the feature that
  // will replace it. A later session edits only between its own two marker lines.

  // >>> listing >>>
  // Old URL, not on the backend. Kept only because the bidding section below still builds on it (S27).
  static const String cropsEndpoint = '/api/crops';
  static const String productListingsEndpoint = '/api/v2/product-listings';
  static String productListingEndpoint(String publicId) => '$productListingsEndpoint/$publicId';
  static const String cropTypesEndpoint = '/api/v2/crop-types';
  static const String farmCropsEndpoint = '/api/v2/farm-crops';
  static const String cropBatchesEndpoint = '/api/v2/crop-batches';
  // <<< listing <<<

  // >>> market >>>
  // The market reads productListingsEndpoint (listing section above); it has no URL of its own.
  // <<< market <<<

  // >>> cart >>>
  // <<< cart <<<

  // >>> payment >>>
  // <<< payment <<<

  // >>> bidding >>>
  static String cropBidsWsUrl(String cropId) => '$wsBaseUrl/ws/bidding/$cropId';
  static String cropBidsEndpoint(String cropId) => '$cropsEndpoint/$cropId/bids';
  // <<< bidding <<<

  // >>> rescue >>>
  static const String rescueCropsEndpoint = '/api/v2/rescue/crops';
  static const String rescueLotsEndpoint = '/api/v2/rescue/lots';
  static String rescueLotEndpoint(String lotId) => '$rescueLotsEndpoint/$lotId';
  static String rescueLotMatchesEndpoint(String lotId) => '${rescueLotEndpoint(lotId)}/matches';
  static String rescueLotSoldEndpoint(String lotId) => '${rescueLotEndpoint(lotId)}/sold';
  static const String rescueSimulateEndpoint = '/api/v2/rescue/simulate';
  static const String rescueAlertsEndpoint = '/api/v2/rescue/alerts';
  static String rescueAlertReadEndpoint(String alertId) => '$rescueAlertsEndpoint/$alertId/read';
  // <<< rescue <<<

  // >>> forecast >>>
  static const String forecastMetaEndpoint = '/api/v2/forecast/meta';
  static const String forecastPriceEndpoint = '/api/v2/forecast/price';
  static const String forecastDemandEndpoint = '/api/v2/forecast/demand';
  // <<< forecast <<<

  // >>> logistics >>>
  // <<< logistics <<<

  // >>> waste >>>
  static const String wasteListingsEndpoint = '/api/waste/listings';
  // <<< waste <<<

  // >>> voice >>>
  // <<< voice <<<
}
