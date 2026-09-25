import 'package:flutter/material.dart';
import '../../widgets/auto_translated_text.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/market_provider.dart';
import '../../localization/l10n_extension.dart';
import '../../widgets/dialogs/ai_assistant_dialog.dart';
import '../../widgets/dialogs/ai_forecast_dialog.dart';
import '../../widgets/dialogs/crop_pre_bidding_dialog.dart';
import '../../widgets/dialogs/waste_to_wealth_dialog.dart';
import '../rescue/publish_rescue_sheet.dart';

class HomeScreen extends StatelessWidget {
  final void Function(String tabId)? onNavigateTab;
  const HomeScreen({super.key, this.onNavigateTab});

  void _go(BuildContext context, String id) => onNavigateTab?.call(id);

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final role = auth.user?.role ?? UserRole.guest;
    final market = context.watch<MarketProvider>();

    return RefreshIndicator(
      color: AppTheme.primaryGreen,
      onRefresh: () async => Future<void>.delayed(const Duration(milliseconds: 350)),
      child: LayoutBuilder(
        builder: (context, constraints) {
          final wide = constraints.maxWidth >= 900;
          return ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: EdgeInsets.symmetric(horizontal: wide ? 32 : 16, vertical: 14),
            children: [
              _greeting(context, auth),
              const SizedBox(height: 16),
              _hero(context),
              const SizedBox(height: 20),
              AutoTranslatedText(context.t('quick_access'), style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
              const SizedBox(height: 10),
              _quickGrid(context, role),
              const SizedBox(height: 18),
              _featureCards(context, role, market),
            ],
          );
        },
      ),
    );
  }

  Widget _greeting(BuildContext context, AuthProvider auth) {
    final logged = auth.isLoggedIn;
    final name = logged && auth.user?.name.trim().isNotEmpty == true ? auth.user!.name : context.t('guest_user');
    return Row(
      children: [
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            AutoTranslatedText(context.t('hello'), style: const TextStyle(fontSize: 12, color: AppTheme.textMuted)),
            AutoTranslatedText(name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
            AutoTranslatedText(context.t('greeting_subtitle'), style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
          ]),
        ),
        InkWell(
          onTap: () => showDialog<void>(context: context, builder: (_) => const AIAssistantDialog()),
          borderRadius: BorderRadius.circular(22),
          child: Container(
            width: 42, height: 42,
            decoration: const BoxDecoration(color: AppTheme.primaryGreen, shape: BoxShape.circle),
            child: const Icon(Icons.auto_awesome_rounded, color: Colors.white, size: 19),
          ),
        ),
      ],
    );
  }

  Widget _hero(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(18),
      child: AspectRatio(
        aspectRatio: 3.2,
        child: Stack(fit: StackFit.expand, children: [
          Image.asset('assets/html_reference/99716b82-eea0-4e13-8939-2b88b46a93cd.webp', fit: BoxFit.cover, filterQuality: FilterQuality.high),
          DecoratedBox(decoration: BoxDecoration(gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Colors.transparent, Colors.black.withValues(alpha: .62)]))),
          Positioned(left: 15, right: 15, bottom: 13, child: AutoTranslatedText(context.t('healthy_farmers'), style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w900))),
        ]),
      ),
    );
  }

  Widget _quickGrid(BuildContext context, UserRole role) {
    final items = <_QuickItem>[];
    if (role == UserRole.farmer || role == UserRole.guest) {
      items.add(_QuickItem('my_crops', Icons.grass_rounded, () {
        if (role == UserRole.guest) {
          _go(context, 'profile');
        } else {
          _go(context, 'my_crops');
        }
      }));
      items.add(_QuickItem('prebid', Icons.gavel_rounded, () => _go(context, 'prebid')));
      items.add(_QuickItem('rescue', Icons.warning_amber_rounded, () => openPublishRescueSheet(context)));
      items.add(_QuickItem('waste_to_wealth', Icons.recycling_rounded, () => showDialog(context: context, builder: (_) => const WasteToWealthDialog())));
    } else if (role == UserRole.buyer) {
      items.add(_QuickItem('market', Icons.storefront_rounded, () => _go(context, 'market')));
      items.add(_QuickItem('my_bids', Icons.gavel_rounded, () => _go(context, 'profile')));
      items.add(_QuickItem('cart', Icons.shopping_cart_outlined, () => _go(context, 'cart')));
      items.add(_QuickItem('orders', Icons.inventory_2_outlined, () => _go(context, 'orders')));
    } else if (role == UserRole.logistics) {
      items.add(_QuickItem('loads', Icons.assignment_outlined, () => _go(context, 'loads')));
      items.add(_QuickItem('trips', Icons.local_shipping_outlined, () => _go(context, 'active')));
      items.add(_QuickItem('earnings', Icons.account_balance_wallet_outlined, () => _go(context, 'earnings')));
      items.add(_QuickItem('profile', Icons.person_outline, () => _go(context, 'profile')));
    } else {
      items.add(_QuickItem('dashboard', Icons.dashboard_outlined, () => _go(context, 'admin_home')));
      items.add(_QuickItem('kyc', Icons.verified_user_outlined, () => _go(context, 'admin_kyc')));
      items.add(_QuickItem('users', Icons.groups_outlined, () => _go(context, 'admin_users')));
      items.add(_QuickItem('payments', Icons.payments_outlined, () => _go(context, 'admin_money')));
    }

    return LayoutBuilder(builder: (context, c) {
      final count = c.maxWidth >= 900 ? 4 : c.maxWidth >= 560 ? 4 : 2;
      return GridView.builder(
        shrinkWrap: true,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: items.length,
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: count, crossAxisSpacing: 9, mainAxisSpacing: 9, childAspectRatio: count == 2 ? 2.0 : 1.35),
        itemBuilder: (_, i) => Material(
          color: Colors.white,
          borderRadius: BorderRadius.circular(15),
          child: InkWell(
            onTap: items[i].onTap,
            borderRadius: BorderRadius.circular(15),
            child: Padding(
              padding: const EdgeInsets.all(10),
              child: Row(children: [
                Container(width: 42, height: 42, decoration: BoxDecoration(color: AppTheme.primaryGreen.withValues(alpha: .09), shape: BoxShape.circle), child: Icon(items[i].icon, color: AppTheme.primaryGreen, size: 21)),
                const SizedBox(width: 9),
                Expanded(child: AutoTranslatedText(context.t(items[i].key), maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800))),
                const Icon(Icons.chevron_right_rounded, size: 18, color: AppTheme.primaryGreen),
              ]),
            ),
          ),
        ),
      );
    });
  }

  Widget _featureCards(BuildContext context, UserRole role, MarketProvider market) {
    return Column(children: [
      _FeatureCard(icon: Icons.auto_awesome_rounded, title: context.t('ai_assistant'), subtitle: context.t('ai_assistant_desc'), onTap: () => showDialog<void>(context: context, builder: (_) => const AIAssistantDialog())),
      const SizedBox(height: 9),
      _FeatureCard(icon: Icons.insights_rounded, title: context.t('market_insights'), subtitle: context.t('market_insights_desc'), onTap: () {
        if (market.crops.isNotEmpty) showDialog<void>(context: context, builder: (_) => AIForecastDialog(crop: market.crops.first));
      }),
      if (role == UserRole.farmer && market.crops.isNotEmpty) ...[
        const SizedBox(height: 9),
        _FeatureCard(icon: Icons.gavel_rounded, title: context.t('set_crop_price'), subtitle: context.t('set_crop_price_desc'), onTap: () => showDialog<void>(context: context, builder: (_) => CropPreBiddingDialog(crop: market.crops.first))),
      ],
    ]);
  }
}

class _QuickItem {
  final String key; final IconData icon; final VoidCallback onTap;
  _QuickItem(this.key, this.icon, this.onTap);
}

class _FeatureCard extends StatelessWidget {
  final IconData icon; final String title; final String subtitle; final VoidCallback onTap;
  const _FeatureCard({required this.icon, required this.title, required this.subtitle, required this.onTap});
  @override
  Widget build(BuildContext context) => Material(
    color: Colors.white,
    borderRadius: BorderRadius.circular(15),
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(15),
      child: Padding(
        padding: const EdgeInsets.all(13),
        child: Row(children: [
          Container(width: 43, height: 43, decoration: BoxDecoration(color: AppTheme.primaryGreen.withValues(alpha: .09), borderRadius: BorderRadius.circular(12)), child: Icon(icon, color: AppTheme.primaryGreen, size: 21)),
          const SizedBox(width: 11),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [AutoTranslatedText(title, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800)), const SizedBox(height: 2), AutoTranslatedText(subtitle, style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted))])),
          const Icon(Icons.chevron_right_rounded, color: AppTheme.primaryGreen),
        ]),
      ),
    ),
  );
}
