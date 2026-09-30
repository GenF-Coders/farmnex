
import 'auto_translated_text.dart';
import 'package:flutter/material.dart';
import '../core/network/forecast_api.dart';
import '../core/theme/app_theme.dart';
import 'ceda_credit.dart';

/// Mandi price strip on the market screen: the forecaster's expected price for tomorrow at a few
/// mandi and crop pairs, against the last recorded price. Own state only; no provider.
class ApmcTickerBar extends StatefulWidget {
  const ApmcTickerBar({super.key});

  @override
  State<ApmcTickerBar> createState() => _ApmcTickerBarState();
}

class _TickerItem {
  final String crop;
  final String market;
  final double price;
  final double changePct;
  const _TickerItem({required this.crop, required this.market, required this.price, required this.changePct});
}

class _ApmcTickerBarState extends State<ApmcTickerBar> {
  static const int _maxItems = 4;

  List<_TickerItem> _items = const [];
  String _credit = '';
  String _asOf = '';
  bool _loading = true;
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final api = ForecastApi();
      final meta = await api.meta();
      final pairs = <List<String>>[];
      for (final m in meta.markets) {
        for (final c in m.crops) {
          if (pairs.length < _maxItems) pairs.add([m.market, c]);
        }
      }
      final found = await Future.wait(pairs.map((p) async {
        try {
          return await api.price(p[0], p[1], days: 1);
        } catch (_) {
          return null; // one pair failing shouldn't blank the strip
        }
      }));
      final items = <_TickerItem>[];
      String asOf = '';
      for (final f in found) {
        if (f == null || f.days.isEmpty) continue;
        final next = f.days.first.expected;
        final last = f.lastPrice;
        items.add(_TickerItem(
          crop: f.crop,
          market: f.market,
          price: next,
          changePct: last == null || last <= 0 ? 0 : ((next - last) / last * 100),
        ));
        asOf = f.asOf;
      }
      if (!mounted) return;
      setState(() {
        _items = items;
        _credit = meta.attribution;
        _asOf = asOf.isNotEmpty ? asOf : meta.dataAsOf;
        _failed = items.isEmpty;
        _loading = false;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _failed = true;
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(color: AppTheme.primaryGreen, shape: BoxShape.circle),
                  ),
                  const SizedBox(width: 6),
                  const AutoTranslatedText(
                    'MANDI PRICE FORECAST',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: AppTheme.textDark, letterSpacing: 0.5),
                  ),
                ],
              ),
              if (_asOf.isNotEmpty)
                AutoTranslatedText(
                  'Data up to $_asOf',
                  style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                ),
            ],
          ),
          const SizedBox(height: 10),
          if (_loading)
            const AutoTranslatedText(
              'Loading mandi forecasts… the first load can take up to a minute.',
              style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
            )
          else if (_failed)
            const AutoTranslatedText(
              'Mandi forecasts are not available right now.',
              style: TextStyle(fontSize: 11, color: AppTheme.textMuted),
            )
          else
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(children: _items.map(_chip).toList()),
            ),
          if (!_loading && !_failed) CedaCredit(text: _credit),
        ],
      ),
    );
  }

  Widget _chip(_TickerItem item) {
    final up = item.changePct >= 0;
    return Container(
      margin: const EdgeInsets.only(right: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Row(
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AutoTranslatedText(item.crop, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
              Text(item.market, style: const TextStyle(fontSize: 10, color: AppTheme.textMuted)),
            ],
          ),
          const SizedBox(width: 14),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('₹${item.price.round()}/q', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: AppTheme.textDark)),
              Text(
                '${up ? '↑ +' : '↓ '}${item.changePct.toStringAsFixed(1)}%',
                style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.bold, color: up ? AppTheme.primaryGreen : Colors.red),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
