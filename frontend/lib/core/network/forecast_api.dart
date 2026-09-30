import 'package:dio/dio.dart';

import '../config/api_config.dart';
import 'api_client.dart';

/// Mandi price forecasts from the FarmNex backend (`/api/v2/forecast`). The app never talks to
/// the forecaster itself; the backend adds the key. The forecaster host sleeps when idle, so the
/// first call can take about a minute: every call here waits up to 100 seconds.
class ForecastApi {
  static final ForecastApi _instance = ForecastApi._();
  factory ForecastApi() => _instance;
  ForecastApi._();

  static const Duration _wait = Duration(seconds: 100);
  static const Duration _metaKeep = Duration(minutes: 10);

  final Dio _dio = ApiClient().dio;
  final Options _options = Options(receiveTimeout: _wait);

  Future<ForecastMeta>? _meta;
  DateTime _metaAt = DateTime.fromMillisecondsSinceEpoch(0);

  /// Lists for the pickers (markets, crops) and the CEDA credit text. Shared by the dialog and the
  /// ticker, and kept for a few minutes so both don't wake the forecaster twice.
  Future<ForecastMeta> meta() {
    final cached = _meta;
    if (cached != null && DateTime.now().difference(_metaAt) < _metaKeep) return cached;
    final fresh = _dio
        .get<dynamic>(ApiConfig.forecastMetaEndpoint, options: _options)
        .then((r) => ForecastMeta.fromJson(r.data as Map<String, dynamic>));
    _meta = fresh;
    _metaAt = DateTime.now();
    fresh.then<void>((_) {}, onError: (Object _) {
      if (identical(_meta, fresh)) _meta = null; // don't keep a failed answer
    });
    return fresh;
  }

  Future<PriceForecast> price(String market, String crop, {int days = 3}) async {
    final r = await _dio.get<dynamic>(
      ApiConfig.forecastPriceEndpoint,
      queryParameters: {'market': market, 'crop': crop, 'days': days},
      options: _options,
    );
    return PriceForecast.fromJson(r.data as Map<String, dynamic>);
  }

  /// HIGH / NORMAL / LOW per crop for one district.
  Future<List<DemandSignal>> demand(String district) async {
    final r = await _dio.get<dynamic>(
      ApiConfig.forecastDemandEndpoint,
      queryParameters: {'district': district},
      options: _options,
    );
    final items = (r.data as Map<String, dynamic>)['items'] as List<dynamic>? ?? const [];
    return items.map((e) => DemandSignal.fromJson(e as Map<String, dynamic>)).toList();
  }
}

double _num(dynamic v) => (v as num?)?.toDouble() ?? 0;
List<String> _strings(dynamic v) => (v as List<dynamic>? ?? const []).map((e) => '$e').toList();

class ForecastMarket {
  final String market;
  final String district;
  final List<String> crops;
  const ForecastMarket({required this.market, required this.district, required this.crops});

  factory ForecastMarket.fromJson(Map<String, dynamic> j) => ForecastMarket(
        market: '${j['market']}',
        district: '${j['district']}',
        crops: _strings(j['crops']),
      );
}

class ForecastMeta {
  final List<ForecastMarket> markets;
  final String attribution;
  final String dataAsOf;
  const ForecastMeta({required this.markets, required this.attribution, required this.dataAsOf});

  factory ForecastMeta.fromJson(Map<String, dynamic> j) => ForecastMeta(
        markets: (j['markets'] as List<dynamic>? ?? const [])
            .map((e) => ForecastMarket.fromJson(e as Map<String, dynamic>))
            .toList(),
        attribution: '${j['attribution'] ?? ''}',
        dataAsOf: '${j['data_as_of'] ?? ''}',
      );

  /// The forecaster's own spelling of a crop for a name like "Onion (प्याज)"; null if it has none.
  String? cropFor(String appName) {
    final name = appName.toLowerCase();
    for (final m in markets) {
      for (final c in m.crops) {
        if (name.contains(c.toLowerCase())) return c;
      }
    }
    return null;
  }

  List<ForecastMarket> marketsFor(String crop) => markets.where((m) => m.crops.contains(crop)).toList();
}

class PriceDay {
  final String date;
  final double low; // p10, Rs per quintal
  final double expected; // p50
  final double high; // p90
  final bool likelyClosed;
  const PriceDay({
    required this.date,
    required this.low,
    required this.expected,
    required this.high,
    required this.likelyClosed,
  });

  factory PriceDay.fromJson(Map<String, dynamic> j) => PriceDay(
        date: '${j['date']}',
        low: _num(j['p10']),
        expected: _num(j['p50']),
        high: _num(j['p90']),
        likelyClosed: j['likely_closed'] == true,
      );
}

class PriceForecast {
  final String market;
  final String crop;
  final String district;
  final String asOf;
  final double? lastPrice;
  final List<PriceDay> days;
  final List<String> reasons;
  final String attribution;
  const PriceForecast({
    required this.market,
    required this.crop,
    required this.district,
    required this.asOf,
    required this.lastPrice,
    required this.days,
    required this.reasons,
    required this.attribution,
  });

  factory PriceForecast.fromJson(Map<String, dynamic> j) => PriceForecast(
        market: '${j['market']}',
        crop: '${j['crop']}',
        district: '${j['district']}',
        asOf: '${j['as_of']}',
        lastPrice: (j['last_price'] as num?)?.toDouble(),
        days: (j['days'] as List<dynamic>? ?? const [])
            .map((e) => PriceDay.fromJson(e as Map<String, dynamic>))
            .toList(),
        reasons: _strings(j['reason']),
        attribution: '${j['attribution'] ?? ''}',
      );
}

class DemandSignal {
  final String crop;
  final String signal; // HIGH, NORMAL or LOW
  final List<String> reasons;
  const DemandSignal({required this.crop, required this.signal, required this.reasons});

  factory DemandSignal.fromJson(Map<String, dynamic> j) => DemandSignal(
        crop: '${j['crop']}',
        signal: '${j['signal']}',
        reasons: _strings(j['reason']),
      );
}

/// A short message for the screen. Never shows the raw exception; the screen translates it.
String forecastErrorMessage(Object error) {
  if (error is DioException) {
    final code = error.response?.statusCode;
    if (code == 401) return 'Please log in to see price forecasts.';
    if (code == 400 || code == 404 || code == 422) {
      final detail = error.response?.data is Map ? (error.response!.data as Map)['detail'] : null;
      if (detail is String && detail.isNotEmpty) return detail;
      return 'No forecast is available for this crop and market.';
    }
    if (code == 503) return 'Price forecasts are temporarily unavailable. Try again soon.';
    if (error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.receiveTimeout) {
      return 'Could not reach the forecaster. Check your internet and try again.';
    }
  }
  return 'Something went wrong. Please try again.';
}
