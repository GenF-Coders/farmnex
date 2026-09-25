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
import '../widgets/dialogs/auth_dialog.dart';
import '../widgets/dialogs/language_selector_dialog.dart';

class MainLayoutScreen extends StatefulWidget {
  const MainLayoutScreen({super.key});
  @override State<MainLayoutScreen> createState() => _MainLayoutScreenState();
}

class _MainLayoutScreenState extends State<MainLayoutScreen> {
  int _index = 0;
  UserRole? _role;
  String _city = 'Pune';

  UserRole _currentRole(BuildContext context) => context.watch<AuthProvider>().user?.role ?? UserRole.guest;

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

    return Scaffold(
      backgroundColor: const Color(0xFFEEF1EA),
      body: SafeArea(
        child: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1280),
            child: Container(
              width: double.infinity,
              height: double.infinity,
              decoration: BoxDecoration(color: const Color(0xFFF7F6F2), borderRadius: BorderRadius.circular(18), boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: .08), blurRadius: 24, offset: const Offset(0, 8))]),
              clipBehavior: Clip.antiAlias,
              child: Column(children: [
                _header(context, auth, lang),
                Expanded(child: IndexedStack(index: _index, children: tabs.map((t) => t.builder(context, _goToTab)).toList())),
                _bottomNav(tabs, lang),
              ]),
            ),
          ),
        ),
      ),
    );
  }

  Widget _header(BuildContext context, AuthProvider auth, LanguageProvider lang) {
    return Container(
      padding: const EdgeInsets.fromLTRB(16, 9, 12, 9),
      decoration: const BoxDecoration(color: Colors.white, border: Border(bottom: BorderSide(color: AppTheme.borderLight))),
      child: LayoutBuilder(builder: (context, c) {
        final compact = c.maxWidth < 600;
        return Row(children: [
          const Icon(Icons.eco_rounded, color: AppTheme.primaryGreen, size: 22),
          const SizedBox(width: 7),
          AutoTranslatedText('FarmNex', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
          const Spacer(),
          _cityDropdown(context, compact),
          const SizedBox(width: 5),
          InkWell(onTap: () => showDialog<void>(context: context, builder: (_) => const LanguageSelectorDialog()), borderRadius: BorderRadius.circular(9), child: Padding(padding: const EdgeInsets.all(7), child: Row(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.language, size: 17, color: AppTheme.primaryGreen), if (!compact) ...[const SizedBox(width: 4), AutoTranslatedText('Language', style: TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800, color: AppTheme.primaryGreen))]]))),
          InkWell(onTap: () => showDialog<void>(context: context, builder: (_) => const AIAssistantDialog()), borderRadius: BorderRadius.circular(9), child: const Padding(padding: EdgeInsets.all(7), child: Icon(Icons.mic_none_rounded, size: 19, color: AppTheme.primaryGreen))),
          InkWell(onTap: () { if (auth.isLoggedIn) _goToTab('profile'); else showDialog<bool>(context: context, builder: (_) => const AuthDialog()); }, borderRadius: BorderRadius.circular(9), child: Padding(padding: const EdgeInsets.all(7), child: Icon(auth.isLoggedIn ? Icons.person_outline_rounded : Icons.login_rounded, size: 20))),
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
      padding: const EdgeInsets.fromLTRB(5, 6, 5, 9),
      decoration: const BoxDecoration(color: Colors.white, border: Border(top: BorderSide(color: AppTheme.borderLight))),
      child: Row(children: [for (var i = 0; i < tabs.length; i++) Expanded(child: InkWell(onTap: () => setState(() => _index = i), borderRadius: BorderRadius.circular(10), child: Padding(padding: const EdgeInsets.symmetric(vertical: 2), child: Column(mainAxisSize: MainAxisSize.min, children: [Icon(i == _index ? tabs[i].activeIcon : tabs[i].icon, size: 19, color: i == _index ? AppTheme.primaryGreen : const Color(0xFF9CA3AF)), const SizedBox(height: 2), AutoTranslatedText(AppTranslationsCompat.label(tabs[i], lang), maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 9.5, fontWeight: i == _index ? FontWeight.w800 : FontWeight.w600, color: i == _index ? AppTheme.primaryGreen : const Color(0xFF9CA3AF)))]))))]),
    );
  }
}

class AppTranslationsCompat {
  static String label(AppTab tab, LanguageProvider lang) => lang.translate(tab.labelKey);
}
