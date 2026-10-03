import '../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/navigation/role_tabs.dart';
import '../core/theme/app_theme.dart';
import '../models/user_model.dart';
import '../providers/auth_provider.dart';
import '../localization/l10n_extension.dart';
import '../localization/city_localization.dart';
import '../localization/language_provider.dart';
import '../widgets/dialogs/ai_assistant_dialog.dart';
import '../widgets/dialogs/language_selector_dialog.dart';

class MainLayoutScreen extends StatefulWidget {
  const MainLayoutScreen({super.key});
  @override State<MainLayoutScreen> createState() => _MainLayoutScreenState();
}

class _MainLayoutScreenState extends State<MainLayoutScreen> {
  int _index = 0;
  UserRole? _role;
  String _city = 'Pune';

  // read, not watch: this runs from a tap, outside build.
  UserRole _currentRole(BuildContext context) {
    final auth = context.read<AuthProvider>();
    return auth.isLoggedIn ? (auth.user?.role ?? UserRole.guest) : UserRole.guest;
  }

  void _goToTab(String id) {
    final tabs = RoleTabs.forRole(_currentRole(context));
    final i = tabs.indexWhere((t) => t.id == id);
    if (i >= 0) setState(() => _index = i);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final lang = context.watch<LanguageProvider>();
    final role = auth.isLoggedIn ? (auth.user?.role ?? UserRole.guest) : UserRole.guest;
    final tabs = RoleTabs.forRole(role);
    if (_role != role) { _role = role; _index = 0; }
    if (_index >= tabs.length) _index = 0;

    final column = Column(children: [
      _header(context, auth, lang),
      Expanded(child: IndexedStack(index: _index, children: tabs.map((t) => t.builder(context, _goToTab)).toList())),
      _bottomNav(tabs, lang),
    ]);
    return Scaffold(
      backgroundColor: AppTheme.backgroundWarm,
      body: SafeArea(
        bottom: false,
        child: LayoutBuilder(builder: (context, c) {
          // Phones use the whole screen; only tablets/desktops get the centred, framed page.
          if (c.maxWidth < 700) return column;
          return Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1280),
              child: Container(
                margin: const EdgeInsets.all(12),
                decoration: BoxDecoration(color: AppTheme.backgroundWarm, borderRadius: BorderRadius.circular(18), boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: .06), blurRadius: 24, offset: const Offset(0, 8))]),
                clipBehavior: Clip.antiAlias,
                child: column,
              ),
            ),
          );
        }),
      ),
    );
  }

  Widget _header(BuildContext context, AuthProvider auth, LanguageProvider lang) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 10, 8, 10),
      decoration: const BoxDecoration(color: Colors.white, border: Border(bottom: BorderSide(color: AppTheme.borderLight))),
      child: LayoutBuilder(builder: (context, c) {
        final compact = c.maxWidth < 600;
        return Row(children: [
          Container(
            width: 34,
            height: 34,
            decoration: BoxDecoration(gradient: AppTheme.brandGradient, borderRadius: BorderRadius.circular(10)),
            child: const Icon(Icons.eco_rounded, color: AppTheme.harvestGold, size: 21),
          ),
          const SizedBox(width: 9),
          AutoTranslatedText('FarmNex', style: TextStyle(fontSize: 21, fontWeight: FontWeight.w900, letterSpacing: -0.5, color: AppTheme.deepGreen)),
          const Spacer(),
          if (!compact) ...[_cityDropdown(context, compact), const SizedBox(width: 4)],
          _HeaderIcon(
            icon: Icons.translate_rounded,
            tooltip: 'Language',
            onTap: () => showDialog<void>(context: context, builder: (_) => const LanguageSelectorDialog()),
          ),
          const SizedBox(width: 4),
          // The ONE way to reach the AI assistant (voice or typing).
          Material(
            color: AppTheme.primaryGreen,
            borderRadius: BorderRadius.circular(22),
            child: InkWell(
              onTap: () => showDialog<void>(context: context, builder: (_) => const AIAssistantDialog()),
              borderRadius: BorderRadius.circular(22),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
                child: Row(mainAxisSize: MainAxisSize.min, children: [
                  const Icon(Icons.auto_awesome_rounded, size: 18, color: Colors.white),
                  const SizedBox(width: 6),
                  AutoTranslatedText('Ask AI', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800, color: Colors.white)),
                ]),
              ),
            ),
          ),
        ]);
      }),
    );
  }

  Widget _cityDropdown(BuildContext context, bool compact) {
    final cities = LocalizedCity.maharashtraCities;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7),
      decoration: BoxDecoration(color: const Color(0xFFF4F7F1), borderRadius: BorderRadius.circular(9), border: Border.all(color: AppTheme.borderLight)),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: _city,
          hint: AutoTranslatedText(context.t('select_city')),
          selectedItemBuilder: (context) => cities.map((city) => Align(alignment: Alignment.centerLeft, child: AutoTranslatedText(compact ? LocalizedCity.name(city, context.languageCode) : '${context.t('select_city')}: ${LocalizedCity.name(city, context.languageCode)}', maxLines: 1, overflow: TextOverflow.ellipsis))).toList(),
          isDense: true,
          icon: const Icon(Icons.keyboard_arrow_down_rounded, size: 17),
          style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.textDark),
          onChanged: (value) { if (value != null) setState(() => _city = value); },
          items: cities.map((city) => DropdownMenuItem<String>(value: city, child: Row(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.location_on_outlined, size: 15, color: AppTheme.primaryGreen), const SizedBox(width: 4), AutoTranslatedText(LocalizedCity.name(city, context.languageCode))]))).toList(),
        ),
      ),
    );
  }

  Widget _bottomNav(List<AppTab> tabs, LanguageProvider lang) {
    return Container(
      decoration: const BoxDecoration(color: Colors.white, border: Border(top: BorderSide(color: AppTheme.borderLight))),
      child: SafeArea(
        top: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(6, 8, 6, 8),
          child: Row(children: [
            for (var i = 0; i < tabs.length; i++)
              Expanded(child: _NavItem(
                icon: i == _index ? tabs[i].activeIcon : tabs[i].icon,
                label: AppTranslationsCompat.label(tabs[i], lang),
                selected: i == _index,
                onTap: () => setState(() => _index = i),
              )),
          ]),
        ),
      ),
    );
  }
}

class _HeaderIcon extends StatelessWidget {
  final IconData icon;
  final String tooltip;
  final VoidCallback onTap;
  const _HeaderIcon({required this.icon, required this.tooltip, required this.onTap});

  @override
  Widget build(BuildContext context) => IconButton(
        onPressed: onTap,
        tooltip: tooltip,
        icon: Icon(icon, size: 24, color: AppTheme.textDark),
        constraints: const BoxConstraints(minWidth: 44, minHeight: 44),
      );
}

/// One bottom-bar item: a pill behind the icon when selected, label always visible.
class _NavItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final bool selected;
  final VoidCallback onTap;
  const _NavItem({required this.icon, required this.label, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final color = selected ? AppTheme.primaryGreen : const Color(0xFF6B7280);
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 2),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            curve: Curves.easeOut,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 5),
            decoration: BoxDecoration(
              color: selected ? AppTheme.primaryGreen.withValues(alpha: .12) : Colors.transparent,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Icon(icon, size: 25, color: color),
          ),
          const SizedBox(height: 4),
          // Long labels (e.g. "Crop Rescue") shrink to fit instead of being cut off.
          FittedBox(
            fit: BoxFit.scaleDown,
            child: AutoTranslatedText(label, maxLines: 1, style: TextStyle(fontSize: 12, fontWeight: selected ? FontWeight.w800 : FontWeight.w600, color: color)),
          ),
        ]),
      ),
    );
  }
}

class AppTranslationsCompat {
  static String label(AppTab tab, LanguageProvider lang) => lang.translate(tab.labelKey);
}
