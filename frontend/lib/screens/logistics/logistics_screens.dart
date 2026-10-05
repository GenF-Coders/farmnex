import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/network/route_api.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/logistics_provider.dart';
import '../../widgets/auto_translated_text.dart';
import '../../widgets/symbol_widgets.dart';
import 'driver_location.dart';
import 'vehicle_dialog.dart';

void _say(BuildContext context, String text, {bool ok = false}) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: AutoTranslatedText(text),
      backgroundColor: ok ? AppTheme.primaryGreen : null,
    ),
  );
}

/// Loads the driver's data once when a logistics screen first opens.
void _loadOnce(BuildContext context) {
  final logistics = context.read<LogisticsProvider>();
  if (!logistics.hasLoaded && !logistics.isLoading) {
    WidgetsBinding.instance.addPostFrameCallback((_) => logistics.load());
  }
}

/// Spinner / error + retry shown instead of the screen body. Returns null when the body can show.
Widget? _gate(BuildContext context, LogisticsProvider logistics) {
  if (!logistics.hasLoaded) {
    if (logistics.error != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AutoTranslatedText(logistics.error!, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              ElevatedButton(onPressed: logistics.load, child: const AutoTranslatedText('🔄  Try again')),
            ],
          ),
        ),
      );
    }
    return const Center(child: CircularProgressIndicator());
  }
  return null;
}

class LogisticsLoadsScreen extends StatefulWidget {
  const LogisticsLoadsScreen({super.key});

  @override
  State<LogisticsLoadsScreen> createState() => _LogisticsLoadsScreenState();
}

class _LogisticsLoadsScreenState extends State<LogisticsLoadsScreen> {
  @override
  void initState() {
    super.initState();
    _loadOnce(context);
  }

  @override
  Widget build(BuildContext context) {
    final logistics = context.watch<LogisticsProvider>();
    final gate = _gate(context, logistics);
    if (gate != null) return gate;

    final vehicle = logistics.vehicle;
    if (vehicle == null) {
      return ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const SymbolEmptyState(symbol: '🚚', message: 'Register your truck to start getting loads.'),
          ElevatedButton(
            onPressed: () async {
              final ok = await showVehicleDialog(context);
              if (ok && context.mounted) _say(context, '🚚 Truck registered', ok: true);
            },
            child: const AutoTranslatedText('➕  Register my truck'),
          ),
        ],
      );
    }

    final trip = logistics.trip;
    return RefreshIndicator(
      onRefresh: logistics.load,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          _statusCard(logistics, vehicle),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: SymbolStat(symbol: '🆕', value: '${logistics.backhaul.length}', caption: 'Return loads'),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: SymbolStat(
                  symbol: '🚚',
                  value: trip == null ? '0' : '1',
                  caption: 'Running',
                  color: AppTheme.accentAmber,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: SymbolStat(
                  symbol: '💰',
                  value: formatRupeesShort(logistics.earningsPending),
                  caption: 'Pending pay',
                  color: AppTheme.accentTeal,
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          if (trip != null)
            const SymbolEmptyState(symbol: '🚚', message: 'You have a trip.\nOpen 🚚 Trips to run it.')
          else if (!logistics.isOnline)
            const SymbolEmptyState(symbol: '🔴', message: 'You are off duty.\nSwitch 🟢 on to find loads.')
          else ...[
            SizedBox(
              height: 46,
              child: ElevatedButton(
                onPressed: logistics.isBusy
                    ? null
                    : () async {
                        final error = await logistics.findLoads();
                        if (!context.mounted) return;
                        _say(context, error ?? '🤝 Trip planned • open 🚚 Trips', ok: error == null);
                      },
                child: const AutoTranslatedText('🔎  Find loads near me'),
              ),
            ),
            const SizedBox(height: 20),
            const SectionHeader(symbol: '↩️', title: 'Return loads near you'),
            if (logistics.backhaul.isEmpty)
              const SymbolEmptyState(symbol: '🛣️', message: 'No return loads right now.\nCheck back shortly.')
            else
              ...logistics.backhaul.map((o) => _BackhaulCard(option: o)),
          ],
          const SizedBox(height: 20),
        ],
      ),
    );
  }

  Widget _statusCard(LogisticsProvider logistics, VehicleModel vehicle) {
    final online = logistics.isOnline;
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: online ? const Color(0xFFF0FDF4) : const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: online ? AppTheme.primaryGreen.withValues(alpha: 0.3) : AppTheme.borderLight),
      ),
      child: Row(
        children: [
          AutoTranslatedText(online ? '🟢' : '🔴', style: const TextStyle(fontSize: 26)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(
                  online ? 'On duty' : 'Off duty',
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900),
                ),
                AutoTranslatedText(
                  '${vehicle.vehicleNumber} • ${vehicle.capacityKg.round()} kg',
                  style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                ),
              ],
            ),
          ),
          Switch(
            value: online,
            onChanged: (logistics.isBusy || vehicle.onTrip)
                ? null
                : (_) async {
                    final error = await logistics.toggleOnline();
                    if (error != null && mounted) _say(context, error);
                  },
          ),
        ],
      ),
    );
  }
}

class _BackhaulCard extends StatelessWidget {
  final BackhaulOption option;
  const _BackhaulCard({required this.option});

  @override
  Widget build(BuildContext context) {
    final logistics = context.read<LogisticsProvider>();
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Expanded(
                child: AutoTranslatedText(
                  '${option.crop} • ${option.weightKg.round()} kg',
                  style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800),
                ),
              ),
              AutoTranslatedText(
                formatRupees(option.estimatedEarning),
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
              ),
            ],
          ),
          const SizedBox(height: 8),
          AutoTranslatedText('🟢 ${option.pickupAddress}', maxLines: 1, overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          AutoTranslatedText('🔴 ${option.dropAddress}', maxLines: 1, overflow: TextOverflow.ellipsis,
              style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          AutoTranslatedText(
            '🛣️ ${option.loadedKm.round()} km  •  📍 ${option.distanceToPickupKm.round()} km to pickup  •  ♻️ saves ${option.emptyKmSaved.round()} empty km',
            style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 42,
            width: double.infinity,
            child: ElevatedButton(
              onPressed: logistics.isBusy
                  ? null
                  : () async {
                      final error = await logistics.acceptBackhaul(option.loadId);
                      if (!context.mounted) return;
                      _say(context, error ?? '🤝 Load accepted • open 🚚 Trips', ok: error == null);
                    },
              child: const AutoTranslatedText('🤝  Accept'),
            ),
          ),
        ],
      ),
    );
  }
}

class LogisticsActiveScreen extends StatefulWidget {
  const LogisticsActiveScreen({super.key});

  @override
  State<LogisticsActiveScreen> createState() => _LogisticsActiveScreenState();
}

/// The trip screen. While a trip is running, the phone's position is sent every 10 seconds.
/// The timer stops when the screen closes or the app goes to the background (no background GPS).
class _LogisticsActiveScreenState extends State<LogisticsActiveScreen> with WidgetsBindingObserver {
  static const Duration _pingEvery = Duration(seconds: 10);
  Timer? _timer;
  bool _inForeground = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _loadOnce(context);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _inForeground = state == AppLifecycleState.resumed;
    if (!_inForeground) _stopPings();
  }

  void _syncPings(bool running) {
    if (running && _inForeground) {
      _timer ??= Timer.periodic(_pingEvery, (_) => _ping());
    } else {
      _stopPings();
    }
  }

  void _stopPings() {
    _timer?.cancel();
    _timer = null;
  }

  Future<void> _ping() async {
    final position = await currentDriverPosition();
    if (position == null || !mounted) return;
    final speed = position.speed.isNaN ? null : position.speed * 3.6; // m/s -> km/h
    await context.read<LogisticsProvider>().sendPing(position.latitude, position.longitude, speedKmph: speed);
  }

  @override
  Widget build(BuildContext context) {
    final logistics = context.watch<LogisticsProvider>();
    final gate = _gate(context, logistics);
    if (gate != null) return gate;

    final trip = logistics.trip;
    final running = trip != null && trip.isRunning;
    // Start or stop the timer after this frame, never while building.
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _syncPings(running);
    });

    if (trip == null) {
      return const SymbolEmptyState(
        symbol: '🛻',
        message: 'No running trips.\nFind loads in 📋 Loads.',
      );
    }

    final next = trip.nextStop;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SectionHeader(symbol: '🚚', title: 'Running trips'),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: AppTheme.borderLight),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: AutoTranslatedText(
                      trip.isBackhaul ? '↩️ Return trip' : '🚚 Pooled trip',
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800),
                    ),
                  ),
                  AutoTranslatedText(
                    formatRupees(trip.estimatedCost),
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              AutoTranslatedText(
                '🛣️ ${trip.totalDistanceKm.round()} km  •  🕐 ${trip.totalDurationMin.round()} min  •  ${trip.isRunning ? '🚚 On the way' : '🆕 Planned'}',
                style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
              ),
              const SizedBox(height: 12),
              ...trip.stops.map(_stopRow),
              const SizedBox(height: 12),
              if (trip.isPlanned)
                Row(
                  children: [
                    Expanded(
                      child: SizedBox(
                        height: 42,
                        child: ElevatedButton(
                          onPressed: logistics.isBusy ? null : () => _run(logistics.startTrip()),
                          child: const AutoTranslatedText('▶️  Start trip'),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    TextButton(
                      onPressed: logistics.isBusy ? null : () => _run(logistics.cancelTrip()),
                      child: const AutoTranslatedText('❌  Cancel'),
                    ),
                  ],
                )
              else if (next != null)
                SizedBox(
                  height: 42,
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: logistics.isBusy ? null : () => _run(logistics.completeStop(next), done: true),
                    child: AutoTranslatedText(next.isPickup ? '📦  Mark picked up' : '✅  Mark delivered'),
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 20),
      ],
    );
  }

  Future<void> _run(Future<String?> action, {bool done = false}) async {
    final error = await action;
    if (!mounted) return;
    if (error != null) {
      _say(context, error);
    } else if (done && context.read<LogisticsProvider>().trip == null) {
      _say(context, '✅ Trip finished • the money is released by the server', ok: true);
    }
  }

  Widget _stopRow(TripStop stop) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          AutoTranslatedText(stop.isDone ? '✅' : (stop.isPickup ? '🟢' : '🔴'), style: const TextStyle(fontSize: 14)),
          const SizedBox(width: 8),
          Expanded(
            child: AutoTranslatedText(
              '${stop.isPickup ? 'Pick up' : 'Drop'}: ${stop.label}',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 11.5,
                fontWeight: FontWeight.w700,
                color: stop.isDone ? AppTheme.textMuted : null,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class LogisticsEarningsScreen extends StatefulWidget {
  const LogisticsEarningsScreen({super.key});

  @override
  State<LogisticsEarningsScreen> createState() => _LogisticsEarningsScreenState();
}

class _LogisticsEarningsScreenState extends State<LogisticsEarningsScreen> {
  @override
  void initState() {
    super.initState();
    _loadOnce(context);
  }

  @override
  Widget build(BuildContext context) {
    final logistics = context.watch<LogisticsProvider>();
    final gate = _gate(context, logistics);
    if (gate != null) return gate;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF0F766E), Color(0xFF166534)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(22),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const AutoTranslatedText('💰  Earned this session',
                  style: TextStyle(fontSize: 12, color: Color(0xFFBBF7D0), fontWeight: FontWeight.w700)),
              const SizedBox(height: 4),
              AutoTranslatedText(
                formatRupees(logistics.earningsPaid),
                style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: Colors.white),
              ),
              const SizedBox(height: 10),
              AutoTranslatedText(
                '⏳ ${formatRupees(logistics.earningsPending)} pending   •   🛣️ ${logistics.kmCovered.round()} km   •   ✅ ${logistics.completedTrips.length} trips',
                style: const TextStyle(fontSize: 11, color: Color(0xFFDCFCE7), fontWeight: FontWeight.w600),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        const SectionHeader(symbol: '🧾', title: 'Completed'),
        if (logistics.completedTrips.isEmpty)
          const SymbolEmptyState(symbol: '🧾', message: 'No completed trips yet.')
        else
          ...logistics.completedTrips.map(
            (trip) => Container(
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: AutoTranslatedText(
                      '🛣️ ${trip.distanceKm.round()} km',
                      style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800),
                    ),
                  ),
                  AutoTranslatedText(
                    '➕ ${formatRupees(trip.earning)}',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
                  ),
                ],
              ),
            ),
          ),
        const SizedBox(height: 20),
      ],
    );
  }
}
