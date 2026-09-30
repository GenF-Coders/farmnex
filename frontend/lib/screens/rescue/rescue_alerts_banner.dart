import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/rescue_provider.dart';
import '../../widgets/auto_translated_text.dart';
import 'rescue_detail_screen.dart';

/// Shows unread Crop Rescue alerts on the farmer's home screen.
/// Asks the server every 30 seconds, only while the farmer is logged in, the app is open and
/// the home tab is the one on screen. For everyone else it draws nothing and makes no calls.
class RescueAlertsBanner extends StatefulWidget {
  const RescueAlertsBanner({super.key});

  @override
  State<RescueAlertsBanner> createState() => _RescueAlertsBannerState();
}

class _RescueAlertsBannerState extends State<RescueAlertsBanner> with WidgetsBindingObserver {
  static const _every = Duration(seconds: 30);

  Timer? _timer;
  bool _appActive = true;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _appActive = state == AppLifecycleState.resumed;
    _sync(shouldPoll: _appActive && _shouldPoll);
  }

  bool get _shouldPoll {
    final auth = context.read<AuthProvider>();
    return auth.isLoggedIn && auth.user?.role == UserRole.farmer && TickerMode.valuesOf(context).enabled;
  }

  void _sync({required bool shouldPoll}) {
    if (shouldPoll && _timer == null) {
      final rescue = context.read<RescueProvider>();
      rescue.refreshAlerts();
      _timer = Timer.periodic(_every, (_) => rescue.refreshAlerts());
    } else if (!shouldPoll && _timer != null) {
      _timer!.cancel();
      _timer = null;
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isFarmer = auth.isLoggedIn && auth.user?.role == UserRole.farmer;
    // TickerMode is false while this tab is hidden behind another one.
    final visible = isFarmer && TickerMode.valuesOf(context).enabled;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _sync(shouldPoll: visible && _appActive);
    });
    if (!isFarmer) return const SizedBox.shrink();

    final unread = context.watch<RescueProvider>().unreadAlerts;
    if (unread.isEmpty) return const SizedBox.shrink();
    final alert = unread.first;
    final spoiled = alert.kind == 'SPOILED';
    final color = spoiled ? AppTheme.alertRed : AppTheme.accentAmber;

    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Material(
        color: color.withValues(alpha: .10),
        borderRadius: BorderRadius.circular(15),
        child: InkWell(
          borderRadius: BorderRadius.circular(15),
          onTap: () {
            context.read<RescueProvider>().markAlertRead(alert.id);
            Navigator.of(context).push<void>(
              MaterialPageRoute(builder: (_) => RescueDetailScreen(lotId: alert.lotId)),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              Icon(Icons.warning_amber_rounded, color: color),
              const SizedBox(width: 10),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  AutoTranslatedText(alert.title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                  AutoTranslatedText(
                    alert.body,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                  ),
                  if (unread.length > 1)
                    AutoTranslatedText(
                      '+${unread.length - 1} more',
                      style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                    ),
                ]),
              ),
              const Icon(Icons.chevron_right_rounded),
            ]),
          ),
        ),
      ),
    );
  }
}
