import 'package:flutter/material.dart';
import '../../widgets/auto_translated_text.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../models/crop_model.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/market_provider.dart';
import '../../localization/l10n_extension.dart';
import '../../widgets/dialogs/ai_forecast_dialog.dart';
import '../../widgets/dialogs/waste_to_wealth_dialog.dart';
import '../rescue/publish_rescue_sheet.dart';
import '../rescue/rescue_alerts_banner.dart';

/// Home for farmers and guests. Only things that are NOT already a bottom tab live here
/// (My Crops, Pre-Bid and Rescue are tabs; the AI assistant is in the top bar).
class HomeScreen extends StatelessWidget {
  final void Function(String tabId)? onNavigateTab;
  const HomeScreen({super.key, this.onNavigateTab});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final role = auth.user?.role ?? UserRole.guest;
    final market = context.watch<MarketProvider>();

    return RefreshIndicator(
      color: AppTheme.primaryGreen,
      onRefresh: () => context.read<MarketProvider>().load(),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final wide = constraints.maxWidth >= 900;
          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: EdgeInsets.fromLTRB(wide ? 32 : 16, 18, wide ? 32 : 16, 28),
            children: [
              _greeting(context, auth),
              const SizedBox(height: 16),
              const RescueAlertsBanner(),
              _hero(context, market.crops.length),
              const SizedBox(height: 24),
              _SectionTitle(context.t('quick_access')),
              const SizedBox(height: 12),
              _actions(context, role),
              const SizedBox(height: 24),
              _SectionTitle(context.t('market_insights')),
              const SizedBox(height: 12),
              _insights(context, market),
            ],
          );
        },
      ),
    );
  }

  /// "Good morning, Ramesh" feels personal; the sun/moon symbol matches the farmer's own day.
  static (String, String) _partOfDay() {
    final h = DateTime.now().hour;
    if (h < 12) return ('Good morning', '🌅');
    if (h < 17) return ('Good afternoon', '☀️');
    return ('Good evening', '🌙');
  }

  Widget _greeting(BuildContext context, AuthProvider auth) {
    final logged = auth.isLoggedIn;
    final name = logged && auth.user?.name.trim().isNotEmpty == true ? auth.user!.name.split(' ').first : context.t('guest_user');
    final (hello, symbol) = _partOfDay();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      AutoTranslatedText('$symbol  $hello', style: const TextStyle(fontSize: 14, color: AppTheme.textMuted, fontWeight: FontWeight.w700)),
      const SizedBox(height: 2),
      AutoTranslatedText(name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: -0.4, color: AppTheme.textDark)),
      const SizedBox(height: 2),
      AutoTranslatedText(context.t('greeting_subtitle'), style: const TextStyle(fontSize: 14, color: AppTheme.textMuted, height: 1.3)),
    ]);
  }

  /// The farmer photo (a friendly face draws the eye) with a warm sunrise wash and a promise of
  /// more income. The only number shown is real: today's open listings from the market.
  Widget _hero(BuildContext context, int listed) {
    return Container(
      decoration: BoxDecoration(borderRadius: BorderRadius.circular(22), boxShadow: AppTheme.softShadow),
      clipBehavior: Clip.antiAlias,
      child: AspectRatio(
        aspectRatio: 1.9,
        child: Stack(fit: StackFit.expand, children: [
          Image.asset('assets/html_reference/99716b82-eea0-4e13-8939-2b88b46a93cd.webp', fit: BoxFit.cover, alignment: Alignment.centerRight, filterQuality: FilterQuality.high),
          DecoratedBox(
            decoration: BoxDecoration(
              gradient: LinearGradient(
                begin: Alignment.centerLeft,
                end: Alignment.centerRight,
                colors: [AppTheme.deepGreen.withValues(alpha: .96), AppTheme.deepGreen.withValues(alpha: .72), AppTheme.deepGreen.withValues(alpha: .05)],
                stops: const [0, .5, 1],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(18, 16, 18, 16),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: AppTheme.harvestGold, borderRadius: BorderRadius.circular(20)),
                child: const AutoTranslatedText('No middlemen', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w900, color: AppTheme.deepGreen)),
              ),
              const Spacer(),
              FractionallySizedBox(
                widthFactor: .56,
                alignment: Alignment.centerLeft,
                child: AutoTranslatedText(context.t('healthy_farmers'),
                    style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900, height: 1.15, letterSpacing: -0.3)),
              ),
              const SizedBox(height: 6),
              FractionallySizedBox(
                widthFactor: .56,
                alignment: Alignment.centerLeft,
                child: AutoTranslatedText(
                  listed > 0 ? '🌾 $listed crops on sale right now' : 'Sell directly to buyers. Earn more.',
                  style: const TextStyle(color: AppTheme.goldSoft, fontSize: 13.5, fontWeight: FontWeight.w700),
                ),
              ),
            ]),
          ),
        ]),
      ),
    );
  }

  /// Two big actions. A guest is sent to login first (both need an account).
  Widget _actions(BuildContext context, UserRole role) {
    final guest = role == UserRole.guest;
    void needLogin(VoidCallback action) => guest ? onNavigateTab?.call('profile') : action();
    final rescue = _ActionTile(
      icon: Icons.warning_amber_rounded,
      color: AppTheme.accentAmber,
      title: context.t('rescue'),
      subtitle: 'Save your crop before it spoils',
      onTap: () => needLogin(() => openPublishRescueSheet(context)),
    );
    final waste = _ActionTile(
      icon: Icons.recycling_rounded,
      color: const Color(0xFFB7791F),
      title: context.t('waste_to_wealth'),
      subtitle: 'Turn crop waste into money',
      onTap: () => needLogin(() => showDialog<void>(context: context, builder: (_) => const WasteToWealthDialog())),
    );
    return IntrinsicHeight(
      child: Row(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Expanded(child: rescue),
        const SizedBox(width: 12),
        Expanded(child: waste),
      ]),
    );
  }

  /// AI price forecast. Uses a listed Tomato if there is one, else any listed crop, else Tomato
  /// (the demo crop every component supports), so the card always opens something.
  Widget _insights(BuildContext context, MarketProvider market) {
    CropItem? crop;
    for (final c in market.crops) {
      if (c.name.toLowerCase().contains('tomato')) {
        crop = c;
        break;
      }
    }
    crop ??= market.crops.isNotEmpty ? market.crops.first : null;
    final name = crop?.name ?? 'Tomato';
    return _WideCard(
      icon: Icons.insights_rounded,
      title: 'Price forecast: $name',
      subtitle: context.t('market_insights_desc'),
      onTap: () => showDialog<void>(
        context: context,
        builder: (_) => crop != null ? AIForecastDialog(crop: crop) : const AIForecastDialog.forCrop(cropName: 'Tomato'),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);
  @override
  Widget build(BuildContext context) =>
      AutoTranslatedText(text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w900, letterSpacing: -0.2, color: AppTheme.textDark));
}

class _ActionTile extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  const _ActionTile({required this.icon, required this.color, required this.title, required this.subtitle, required this.onTap});

  @override
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(18), boxShadow: AppTheme.softShadow),
        child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(18),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(18), border: Border.all(color: const Color(0xFFEFEBE3))),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(color: color.withValues(alpha: .12), borderRadius: BorderRadius.circular(14)),
                child: Icon(icon, color: color, size: 26),
              ),
              const SizedBox(height: 14),
              AutoTranslatedText(title, maxLines: 2, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, height: 1.2, color: AppTheme.textDark)),
              const SizedBox(height: 4),
              AutoTranslatedText(subtitle, maxLines: 3, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.3)),
            ]),
          ),
        ),
        ),
      );
}

class _WideCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  const _WideCard({required this.icon, required this.title, required this.subtitle, required this.onTap});

  @override
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(borderRadius: BorderRadius.circular(18), boxShadow: AppTheme.softShadow),
        child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(18),
          child: Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(borderRadius: BorderRadius.circular(18), border: Border.all(color: const Color(0xFFEFEBE3))),
            child: Row(children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(color: AppTheme.primaryGreen.withValues(alpha: .1), borderRadius: BorderRadius.circular(14)),
                child: Icon(icon, color: AppTheme.primaryGreen, size: 26),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  AutoTranslatedText(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
                  const SizedBox(height: 3),
                  AutoTranslatedText(subtitle, style: const TextStyle(fontSize: 13, color: AppTheme.textMuted, height: 1.3)),
                ]),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right_rounded, color: AppTheme.primaryGreen, size: 26),
            ]),
          ),
        ),
        ),
      );
}
