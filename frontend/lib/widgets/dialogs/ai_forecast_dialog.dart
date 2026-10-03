import 'dart:async';

import '../auto_translated_text.dart';
import 'package:flutter/material.dart';
import '../../core/network/forecast_api.dart';
import '../../core/theme/app_theme.dart';
import '../../models/crop_model.dart';
import '../ceda_credit.dart';

/// Price forecast for one crop: the next 3 days at a chosen mandi, the demand signal for that
/// mandi's district, the reasons, and the CEDA credit. Everything comes from `/api/v2/forecast`.
class AIForecastDialog extends StatefulWidget {
  /// The listing the forecast was opened from, or null when opened for a crop name only (Home).
  final CropItem? crop;
  final String cropName;
  final String emoji;

  AIForecastDialog({super.key, required CropItem this.crop})
      : cropName = crop.name,
        emoji = crop.emoji;

  /// A forecast without a listing, e.g. Home -> Market insights before anything is listed.
  const AIForecastDialog.forCrop({super.key, required this.cropName, this.emoji = '🍅'}) : crop = null;

  @override
  State<AIForecastDialog> createState() => _AIForecastDialogState();
}

class _AIForecastDialogState extends State<AIForecastDialog> {
  final ForecastApi _api = ForecastApi();

  ForecastMeta? _meta;
  String? _crop; // the forecaster's spelling, e.g. "Onion"
  ForecastMarket? _market;
  PriceForecast? _forecast;
  DemandSignal? _demand;
  String? _error;
  bool _loading = true;
  bool _slow = false; // the forecaster is probably waking up
  Timer? _slowTimer;

  @override
  void initState() {
    super.initState();
    _start();
  }

  @override
  void dispose() {
    _slowTimer?.cancel();
    super.dispose();
  }

  void _busy() {
    _slowTimer?.cancel();
    setState(() {
      _loading = true;
      _slow = false;
      _error = null;
    });
    _slowTimer = Timer(const Duration(seconds: 6), () {
      if (mounted && _loading) setState(() => _slow = true);
    });
  }

  void _idle() {
    _slowTimer?.cancel();
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _start() async {
    _busy();
    try {
      final meta = await _api.meta();
      if (!mounted) return;
      _meta = meta;
      _crop = meta.cropFor(widget.cropName);
      final markets = _crop == null ? <ForecastMarket>[] : meta.marketsFor(_crop!);
      if (markets.isNotEmpty) {
        _market = markets.first;
        await _load();
      }
    } catch (e) {
      if (mounted) _error = forecastErrorMessage(e);
    }
    _idle();
  }

  Future<void> _load() async {
    final market = _market;
    final crop = _crop;
    if (market == null || crop == null) return;
    try {
      final results = await Future.wait<Object?>([
        _api.price(market.market, crop),
        _api.demand(market.district).then<DemandSignal?>((list) {
          for (final d in list) {
            if (d.crop == crop) return d;
          }
          return null;
        }).catchError((Object _) => null), // demand is a bonus; the price still shows without it
      ]);
      if (!mounted) return;
      _forecast = results[0] as PriceForecast;
      _demand = results[1] as DemandSignal?;
    } catch (e) {
      if (mounted) {
        _forecast = null;
        _demand = null;
        _error = forecastErrorMessage(e);
      }
    }
  }

  Future<void> _pickMarket(ForecastMarket market) async {
    _market = market;
    _forecast = null;
    _demand = null;
    _busy();
    await _load();
    _idle();
  }

  @override
  Widget build(BuildContext context) {
    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      backgroundColor: Colors.white,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 540, maxHeight: 720),
        child: Column(
          children: [
            _header(context),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  _cropSummary(),
                  const SizedBox(height: 16),
                  ..._body(),
                  CedaCredit(text: _forecast?.attribution.isNotEmpty == true ? _forecast!.attribution : (_meta?.attribution ?? '')),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _header(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      decoration: const BoxDecoration(
        gradient: LinearGradient(colors: [Color(0xFF166534), Color(0xFF0F766E)]),
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.2),
              borderRadius: BorderRadius.circular(12),
            ),
            child: const Icon(Icons.auto_awesome, color: Color(0xFFFDE047), size: 22),
          ),
          const SizedBox(width: 12),
          const Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(
                  'AI Mandi Price Forecast',
                  style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w800),
                ),
                AutoTranslatedText(
                  'Next 3 days, from real mandi data',
                  style: TextStyle(color: Color(0xFFCCFBF1), fontSize: 11),
                ),
              ],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.close, color: Colors.white),
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
    );
  }

  Widget _cropSummary() {
    final demand = _demand;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Row(
              children: [
                AutoTranslatedText(widget.emoji, style: const TextStyle(fontSize: 28)),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      AutoTranslatedText(widget.cropName, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                      AutoTranslatedText(
                        widget.crop == null
                            ? 'AI price forecast'
                            : 'Listed at ₹${widget.crop!.currentPrice.toInt()} / ${widget.crop!.unit}',
                        style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          if (demand != null)
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                const AutoTranslatedText('Demand', style: TextStyle(fontSize: 10, color: AppTheme.textMuted)),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _demandColor(demand.signal).withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: AutoTranslatedText(
                    _demandLabel(demand.signal),
                    style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: _demandColor(demand.signal)),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  static String _demandLabel(String signal) =>
      signal == 'HIGH' ? 'High' : (signal == 'LOW' ? 'Low' : 'Normal');

  static Color _demandColor(String signal) =>
      signal == 'HIGH' ? AppTheme.primaryGreen : (signal == 'LOW' ? Colors.red : AppTheme.accentAmber);

  List<Widget> _body() {
    if (_loading) {
      return [
        const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator())),
        if (_slow)
          const Center(
            child: AutoTranslatedText(
              'Waking up the forecaster… this can take up to a minute.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 12, color: AppTheme.textMuted),
            ),
          ),
      ];
    }
    final meta = _meta;
    if (meta != null && _error == null && _market == null) {
      return [
        const AutoTranslatedText(
          'No mandi forecast is available for this crop yet.',
          style: TextStyle(fontSize: 13, color: AppTheme.textMuted),
        ),
      ];
    }
    final widgets = <Widget>[];
    if (_crop != null && meta != null) {
      final markets = meta.marketsFor(_crop!);
      if (markets.length > 1) {
        widgets.add(Wrap(
          spacing: 8,
          children: [
            for (final m in markets)
              ChoiceChip(
                label: Text(m.market),
                selected: m.market == _market?.market,
                onSelected: (_) => _pickMarket(m),
              ),
          ],
        ));
        widgets.add(const SizedBox(height: 12));
      }
    }
    if (_error != null) {
      widgets.add(AutoTranslatedText(_error!, style: const TextStyle(fontSize: 13, color: Colors.red)));
      widgets.add(const SizedBox(height: 8));
      widgets.add(Align(
        alignment: Alignment.centerLeft,
        child: TextButton(
          onPressed: () async {
            if (_meta == null) {
              await _start();
            } else {
              _busy();
              await _load();
              _idle();
            }
          },
          child: const AutoTranslatedText('Try again'),
        ),
      ));
    }
    final forecast = _forecast;
    if (forecast != null) widgets.addAll(_forecastView(forecast));
    return widgets;
  }

  List<Widget> _forecastView(PriceForecast f) {
    final top = f.days.fold<double>(0, (m, d) => d.high > m ? d.high : m);
    return [
      Row(
        children: [
          const Icon(Icons.bar_chart, color: AppTheme.primaryGreen, size: 18),
          const SizedBox(width: 6),
          Expanded(
            child: AutoTranslatedText(
              '${f.crop} at ${f.market} (₹ per quintal)',
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
      const SizedBox(height: 12),
      Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppTheme.borderLight),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [for (final d in f.days) _dayBar(d, top)],
        ),
      ),
      const SizedBox(height: 6),
      AutoTranslatedText(
        'Based on mandi data up to ${f.asOf}. Bar = expected price; range = low to high.',
        style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
      ),
      if (f.reasons.isNotEmpty) ...[
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: const Color(0xFFECFDF5),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: const Color(0xFFA7F3D0)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const AutoTranslatedText(
                'Why this forecast',
                style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.bold, color: Color(0xFF065F46)),
              ),
              const SizedBox(height: 4),
              for (final r in f.reasons)
                Padding(
                  padding: const EdgeInsets.only(top: 3),
                  child: AutoTranslatedText('• $r', style: const TextStyle(fontSize: 11.5, color: Color(0xFF047857), height: 1.3)),
                ),
            ],
          ),
        ),
      ],
    ];
  }

  Widget _dayBar(PriceDay d, double top) {
    final barHeight = top <= 0 ? 20.0 : 20.0 + 70.0 * (d.expected / top);
    return Column(
      mainAxisAlignment: MainAxisAlignment.end,
      children: [
        Text('₹${d.expected.round()}', style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
        Text('${d.low.round()}–${d.high.round()}', style: const TextStyle(fontSize: 8.5, color: AppTheme.textMuted)),
        const SizedBox(height: 4),
        Container(
          width: 32,
          height: barHeight,
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.bottomCenter,
              end: Alignment.topCenter,
              colors: [AppTheme.primaryGreen.withValues(alpha: 0.5), AppTheme.primaryGreen],
            ),
            borderRadius: BorderRadius.circular(6),
          ),
        ),
        const SizedBox(height: 6),
        Text(d.date.length >= 10 ? d.date.substring(5) : d.date, style: const TextStyle(fontSize: 9, color: AppTheme.textMuted)),
        if (d.likelyClosed) const Text('closed?', style: TextStyle(fontSize: 8, color: Colors.red)),
      ],
    );
  }
}
