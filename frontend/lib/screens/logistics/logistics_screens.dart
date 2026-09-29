import '../../widgets/auto_translated_text.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../localization/l10n_extension.dart';
import '../../providers/logistics_provider.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/symbol_widgets.dart';

class LogisticsLoadsScreen extends StatefulWidget {
  const LogisticsLoadsScreen({super.key});

  @override
  State<LogisticsLoadsScreen> createState() => _LogisticsLoadsScreenState();
}

class _LogisticsLoadsScreenState extends State<LogisticsLoadsScreen> {
  String _selectedCity = 'All Maharashtra';

  static const List<String> _maharashtraCities = [
    'All Maharashtra', 'Pune', 'Mumbai', 'Navi Mumbai', 'Thane', 'Nagpur', 'Nashik',
    'Chhatrapati Sambhajinagar', 'Kolhapur', 'Solapur', 'Sangli', 'Satara', 'Latur',
    'Nanded', 'Jalgaon', 'Dhule', 'Ahmednagar', 'Amravati', 'Akola', 'Beed',
    'Buldhana', 'Chandrapur', 'Parbhani', 'Osmanabad', 'Ratnagiri', 'Sindhudurg',
    'Wardha', 'Yavatmal', 'Washim', 'Gondia', 'Bhandara', 'Palghar', 'Raigad',
  ];

  @override
  Widget build(BuildContext context) {
    final logistics = context.watch<LogisticsProvider>();
    final allLoads = logistics.availableTrips;
    final loads = _selectedCity == 'All Maharashtra'
        ? allLoads
        : allLoads.where((trip) =>
            trip.pickup.contains(_selectedCity) || trip.drop.contains(_selectedCity)).toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [

        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: logistics.isOnline ? const Color(0xFFF0FDF4) : const Color(0xFFF9FAFB),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: logistics.isOnline
                  ? AppTheme.primaryGreen.withValues(alpha: 0.3)
                  : AppTheme.borderLight,
            ),
          ),
          child: Row(
            children: [
              AutoTranslatedText(logistics.isOnline ? '🟢' : '🔴', style: const TextStyle(fontSize: 26)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      logistics.isOnline ? 'On duty' : 'Off duty',
                      style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900),
                    ),
                    AutoTranslatedText(
                      logistics.isOnline ? '🚚 Receiving load offers' : '⏸️ Offers paused',
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              Switch(
                value: logistics.isOnline,
                onChanged: (_) => logistics.toggleOnline(),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(14),
            border: Border.all(color: AppTheme.borderLight),
          ),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              isExpanded: true,
              value: _selectedCity,
              icon: const Icon(Icons.keyboard_arrow_down_rounded),
              items: _maharashtraCities
                  .map((city) => DropdownMenuItem<String>(value: city, child: AutoTranslatedText(city, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700))))
                  .toList(),
              onChanged: (city) => setState(() => _selectedCity = city ?? _selectedCity),
            ),
          ),
        ),
        const SizedBox(height: 14),

        Row(
          children: [
            Expanded(child: SymbolStat(symbol: '🆕', value: '${loads.length}', caption: 'Open loads')),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '🚚',
                value: '${logistics.activeTrips.length}',
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

        SectionHeader(symbol: '📋', title: _selectedCity == 'All Maharashtra' ? 'Loads in Maharashtra' : 'Loads near $_selectedCity'),
        if (!logistics.isOnline)
          const SymbolEmptyState(symbol: '🔴', message: 'You are off duty.\nSwitch 🟢 on to see loads.')
        else if (loads.isEmpty)
          const SymbolEmptyState(symbol: '🛣️', message: 'No open loads right now.\nCheck back shortly.')
        else
          ...loads.map((trip) => _TripCard(
                trip: trip,
                primaryLabel: '🤝  Accept',
                onPrimary: () {
                  logistics.accept(trip.id);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: AutoTranslatedText('🤝 Load accepted • ${formatRupees(trip.payout)} on delivery'),
                      backgroundColor: AppTheme.primaryGreen,
                    ),
                  );
                },
              )),
        const SizedBox(height: 20),
      ],
    );
  }
}

class LogisticsActiveScreen extends StatelessWidget {
  const LogisticsActiveScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final logistics = context.watch<LogisticsProvider>();
    final trips = logistics.activeTrips;

    if (trips.isEmpty) {
      return const SymbolEmptyState(
        symbol: '🛻',
        message: 'No running trips.\nAccept a load from 📋 Loads.',
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const SectionHeader(symbol: '🚚', title: 'Running trips'),
        ...trips.map((trip) {

          final String label;
          final VoidCallback action;
          if (trip.status == 'accepted') {
            label = '📦  Mark picked up';
            action = () => logistics.markPicked(trip.id);
          } else if (trip.status == 'picked') {
            label = '🚚  Start transit';
            action = () => logistics.startTransit(trip.id);
          } else {
            label = '✅  Deliver (OTP)';
            action = () => _askOtp(context, trip);
          }

          return _TripCard(
            trip: trip,
            primaryLabel: label,
            onPrimary: action,
            showProgress: true,
          );
        }),
        const SizedBox(height: 20),
      ],
    );
  }

  void _askOtp(BuildContext context, DeliveryTrip trip) {
    final controller = TextEditingController();
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(22)),
        title: const Row(
          children: [
            AutoTranslatedText('🔐', style: TextStyle(fontSize: 22)),
            SizedBox(width: 10),
            AutoTranslatedText('Delivery OTP', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AutoTranslatedText(
              context.t('delivery_otp'),
              style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
            ),

            if (kDebugMode)
              AutoTranslatedText(
                'debug: ${trip.otp}',
                style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
              ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              keyboardType: TextInputType.number,
              maxLength: 4,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: 8),
              decoration: const InputDecoration(counterText: '', hintText: '••••'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: AutoTranslatedText('❌  Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final logistics = dialogContext.read<LogisticsProvider>();
              final payments = dialogContext.read<PaymentProvider>();
              final ok = logistics.confirmDelivery(trip.id, controller.text);
              Navigator.of(dialogContext).pop();
              if (ok) {

                payments.releaseEscrow(trip.orderId);
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: AutoTranslatedText('✅ Delivered • 🔓 escrow released • ${formatRupees(trip.payout)} credited'),
                    backgroundColor: AppTheme.primaryGreen,
                  ),
                );
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: AutoTranslatedText('❌ Wrong OTP. Ask the buyer again.')),
                );
              }
            },
            style: ElevatedButton.styleFrom(minimumSize: const Size(120, 42)),
            child: AutoTranslatedText('✅  Verify'),
          ),
        ],
      ),
    );
  }
}

class LogisticsEarningsScreen extends StatelessWidget {
  const LogisticsEarningsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final logistics = context.watch<LogisticsProvider>();

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
              AutoTranslatedText('💰  Paid out',
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
                  AutoTranslatedText(trip.emoji, style: const TextStyle(fontSize: 22)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AutoTranslatedText(trip.cropName,
                            style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800)),
                        AutoTranslatedText(
                          '📍 ${trip.pickup.split(',').first} ➜ ${trip.drop.split(',').first}  •  🛣️ ${trip.distanceKm.round()} km',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                        ),
                      ],
                    ),
                  ),
                  AutoTranslatedText(
                    '➕ ${formatRupees(trip.payout)}',
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

class _TripCard extends StatelessWidget {
  final DeliveryTrip trip;
  final String primaryLabel;
  final VoidCallback onPrimary;
  final bool showProgress;

  const _TripCard({
    required this.trip,
    required this.primaryLabel,
    required this.onPrimary,
    this.showProgress = false,
  });

  @override
  Widget build(BuildContext context) {
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
              AutoTranslatedText(trip.emoji, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      trip.cropName,
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800),
                    ),
                    AutoTranslatedText(
                      '🆔 ${trip.orderId}  •  🕐 ${trip.scheduledFor}',
                      style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              AutoTranslatedText(
                formatRupees(trip.payout),
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
              ),
            ],
          ),
          const SizedBox(height: 12),

          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Column(
                children: [
                  AutoTranslatedText('🟢', style: TextStyle(fontSize: 11)),
                  SizedBox(
                    height: 18,
                    child: VerticalDivider(width: 10, thickness: 1.2, color: AppTheme.borderLight),
                  ),
                  AutoTranslatedText('🔴', style: TextStyle(fontSize: 11)),
                ],
              ),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      trip.pickup,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 14),
                    AutoTranslatedText(
                      trip.drop,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),

          Row(
            children: [
              _chip('🛣️', '${trip.distanceKm.round()} km'),
              _chip('⚖️', '${trip.weightQuintal.round()} q'),
              _chip(trip.vehicleNeeded.substring(0, 2), trip.vehicleNeeded.substring(2).trim()),
              if (showProgress) _chip(trip.statusSymbol, ''),
            ],
          ),
          const SizedBox(height: 12),

          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 42,
                  child: ElevatedButton(onPressed: onPrimary, child: AutoTranslatedText(primaryLabel)),
                ),
              ),
              const SizedBox(width: 8),
              _square('🗺️', 'Navigate', () {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: AutoTranslatedText('🗺️ ${trip.pickup} ➜ ${trip.drop}')),
                );
              }),
              _square('📞', 'Call', () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: AutoTranslatedText('📞 Calling the farmer…')),
                );
              }),
            ],
          ),
        ],
      ),
    );
  }

  Widget _chip(String symbol, String label) {
    return Container(
      margin: const EdgeInsets.only(right: 6),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: AutoTranslatedText(
        label.isEmpty ? symbol : '$symbol $label',
        style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700),
      ),
    );
  }

  Widget _square(String symbol, String tooltip, VoidCallback onTap) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          width: 42,
          height: 42,
          margin: const EdgeInsets.only(left: 6),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: const Color(0xFFF9FAFB),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.borderLight),
          ),
          child: AutoTranslatedText(symbol, style: const TextStyle(fontSize: 17)),
        ),
      ),
    );
  }
}
