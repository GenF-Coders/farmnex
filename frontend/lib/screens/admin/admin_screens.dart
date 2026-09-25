import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/user_model.dart';
import '../../providers/admin_provider.dart';
import '../../widgets/symbol_widgets.dart';

class AdminDashboardScreen extends StatelessWidget {
  final void Function(String tabId)? onNavigate;

  const AdminDashboardScreen({super.key, this.onNavigate});

  @override
  Widget build(BuildContext context) {
    final admin = context.watch<AdminProvider>();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFF064E3B), Color(0xFF1C1917)],
            ),
            borderRadius: BorderRadius.circular(22),
          ),
          child: Row(
            children: [
              AutoTranslatedText('🛡️', style: TextStyle(fontSize: 30)),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      'APMC Control Room',
                      style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: Colors.white),
                    ),
                    AutoTranslatedText(
                      '🔒 ${formatRupeesShort(admin.escrowLocked)} locked  •  ✅ ${formatRupeesShort(admin.settledToday)} settled',
                      style: const TextStyle(fontSize: 11, color: Color(0xFFA7F3D0)),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        const SectionHeader(symbol: '📈', title: 'Platform'),
        Row(
          children: [
            Expanded(child: SymbolStat(symbol: '🧑‍🌾', value: '${admin.farmerCount}', caption: 'Farmers')),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '🏢',
                value: '${admin.buyerCount}',
                caption: 'Buyers',
                color: AppTheme.accentTeal,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '🚚',
                value: '${admin.logisticsCount}',
                caption: 'Transporters',
                color: AppTheme.accentAmber,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: SymbolStat(
                symbol: '📋',
                value: '${admin.pendingKycCount}',
                caption: 'KYC pending',
                color: AppTheme.alertRed,
                onTap: () => onNavigate?.call('admin_kyc'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '🔒',
                value: formatRupeesShort(admin.escrowLocked),
                caption: 'In escrow',
                color: AppTheme.accentAmber,
                onTap: () => onNavigate?.call('admin_money'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '🚫',
                value: '${admin.suspendedCount}',
                caption: 'Suspended',
                color: AppTheme.alertRed,
                onTap: () => onNavigate?.call('admin_users'),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        const SectionHeader(symbol: '⚡', title: 'Quick actions'),
        Row(
          children: [
            Expanded(
              child: SymbolAction(
                symbol: '✅',
                label: 'KYC',
                badge: admin.pendingKycCount > 0 ? '${admin.pendingKycCount}' : null,
                onTap: () => onNavigate?.call('admin_kyc'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolAction(
                symbol: '👥',
                label: 'Users',
                color: AppTheme.accentTeal,
                onTap: () => onNavigate?.call('admin_users'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolAction(
                symbol: '💳',
                label: 'Money',
                color: AppTheme.accentAmber,
                onTap: () => onNavigate?.call('admin_money'),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolAction(
                symbol: '📢',
                label: 'Notice',
                color: AppTheme.alertRed,
                onTap: () => ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: AutoTranslatedText('📢 Broadcast composer — POST /api/admin/broadcast')),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        const SectionHeader(symbol: '🕐', title: 'Latest KYC'),
        ...admin.pendingKyc.take(2).map((k) => _KycTile(request: k)),
        const SizedBox(height: 20),
      ],
    );
  }
}

class AdminKycScreen extends StatelessWidget {
  const AdminKycScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final admin = context.watch<AdminProvider>();
    final pending = admin.pendingKyc;
    final decided = admin.kycQueue.where((k) => k.status != 'pending').toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        SectionHeader(
          symbol: '⏳',
          title: 'Pending',
          trailing: StatusPill(symbol: '📋', label: '${pending.length}', color: AppTheme.accentAmber),
        ),
        if (pending.isEmpty)
          const SymbolEmptyState(symbol: '🎉', message: 'Queue is clear.\nEvery application is reviewed.')
        else
          ...pending.map((k) => _KycTile(request: k)),
        if (decided.isNotEmpty) ...[
          const SizedBox(height: 16),
          const SectionHeader(symbol: '🗂️', title: 'Decided'),
          ...decided.map((k) => _KycTile(request: k)),
        ],
        const SizedBox(height: 20),
      ],
    );
  }
}

class _KycTile extends StatelessWidget {
  final KycRequest request;

  const _KycTile({required this.request});

  @override
  Widget build(BuildContext context) {
    final admin = context.read<AdminProvider>();
    final pending = request.status == 'pending';

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
              AutoTranslatedText(request.roleSymbol, style: const TextStyle(fontSize: 24)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      request.applicantName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800),
                    ),
                    AutoTranslatedText(
                      '${request.documentType}  •  🕐 ${request.submittedAgo}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              if (!pending)
                StatusPill(
                  symbol: request.status == 'approved' ? '✅' : '❌',
                  label: request.status == 'approved' ? 'Approved' : 'Rejected',
                  color: request.status == 'approved' ? AppTheme.primaryGreen : AppTheme.alertRed,
                ),
            ],
          ),
          const SizedBox(height: 10),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: const Color(0xFFF9FAFB),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                AutoTranslatedText('🆔', style: TextStyle(fontSize: 14)),
                const SizedBox(width: 8),
                Expanded(
                  child: AutoTranslatedText(
                    request.documentNumber,
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 0.4),
                  ),
                ),
                AutoTranslatedText('📎', style: TextStyle(fontSize: 14)),
              ],
            ),
          ),
          if (pending) ...[
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 40,
                    child: OutlinedButton(
                      onPressed: () => admin.rejectKyc(request.id),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: AppTheme.alertRed,
                        side: BorderSide(color: AppTheme.alertRed.withValues(alpha: 0.4)),
                      ),
                      child: AutoTranslatedText('❌  Reject'),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SizedBox(
                    height: 40,
                    child: ElevatedButton(
                      onPressed: () {
                        admin.approveKyc(request.id);
                        ScaffoldMessenger.of(context).showSnackBar(
                          SnackBar(
                            content: AutoTranslatedText('✅ ${request.applicantName} verified.'),
                            backgroundColor: AppTheme.primaryGreen,
                          ),
                        );
                      },
                      child: AutoTranslatedText('✅  Approve'),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

class AdminUsersScreen extends StatefulWidget {
  const AdminUsersScreen({super.key});

  @override
  State<AdminUsersScreen> createState() => _AdminUsersScreenState();
}

class _AdminUsersScreenState extends State<AdminUsersScreen> {
  UserRole? _filter;

  @override
  Widget build(BuildContext context) {
    final admin = context.watch<AdminProvider>();
    final users = _filter == null
        ? admin.users
        : admin.users.where((u) => u.role == _filter).toList();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              _filterChip(null, '👥', 'All'),
              _filterChip(UserRole.farmer, '🧑‍🌾', 'Farmers'),
              _filterChip(UserRole.buyer, '🏢', 'Buyers'),
              _filterChip(UserRole.logistics, '🚚', 'Transport'),
            ],
          ),
        ),
        const SizedBox(height: 16),
        ...users.map(
          (user) => Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: Row(
              children: [
                AutoTranslatedText(user.roleSymbol, style: const TextStyle(fontSize: 22)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Flexible(
                            child: AutoTranslatedText(
                              user.name,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                            ),
                          ),
                          const SizedBox(width: 6),
                          AutoTranslatedText(user.isVerified ? '✅' : '⏳', style: const TextStyle(fontSize: 12)),
                        ],
                      ),
                      AutoTranslatedText(
                        '📍 ${user.location}  •  🤝 ${user.trades} trades',
                        style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                      ),
                    ],
                  ),
                ),
                Tooltip(
                  message: user.isSuspended ? 'Restore' : 'Suspend',
                  child: InkWell(
                    onTap: () => context.read<AdminProvider>().toggleSuspend(user.id),
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      width: 38,
                      height: 34,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: (user.isSuspended ? AppTheme.alertRed : AppTheme.borderLight)
                            .withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: AutoTranslatedText(
                        user.isSuspended ? '🔓' : '🚫',
                        style: const TextStyle(fontSize: 15),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 20),
      ],
    );
  }

  Widget _filterChip(UserRole? role, String symbol, String label) {
    final selected = _filter == role;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: AutoTranslatedText('$symbol $label', style: const TextStyle(fontSize: 12)),
        selected: selected,
        onSelected: (_) => setState(() => _filter = role),
        selectedColor: AppTheme.primaryGreen.withValues(alpha: 0.15),
      ),
    );
  }
}

class AdminMoneyScreen extends StatelessWidget {
  const AdminMoneyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final admin = context.watch<AdminProvider>();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Row(
          children: [
            Expanded(
              child: SymbolStat(
                symbol: '🔒',
                value: formatRupeesShort(admin.escrowLocked),
                caption: 'Escrow held',
                color: AppTheme.accentAmber,
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '✅',
                value: formatRupeesShort(admin.settledToday),
                caption: 'Settled',
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: SymbolStat(
                symbol: '⚙️',
                value: formatRupeesShort((admin.settledToday + admin.escrowLocked) * 0.01),
                caption: 'Platform fee',
                color: AppTheme.accentTeal,
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),
        const SectionHeader(symbol: '💳', title: 'Settlement feed'),
        ...admin.settlements.map(
          (row) => Container(
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: Row(
              children: [
                AutoTranslatedText(row.symbol, style: const TextStyle(fontSize: 20)),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      AutoTranslatedText(
                        row.party,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700),
                      ),
                      AutoTranslatedText('🕐 ${row.ago}', style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted)),
                    ],
                  ),
                ),
                AutoTranslatedText(
                  formatRupees(row.amount),
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900),
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
