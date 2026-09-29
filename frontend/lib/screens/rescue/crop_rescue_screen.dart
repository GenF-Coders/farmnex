import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../localization/l10n_extension.dart';
import '../../models/rescue_listing_model.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/rescue_provider.dart';
import '../../widgets/symbol_widgets.dart';
import '../../widgets/crop_media_uploader.dart';
import 'publish_rescue_sheet.dart';
import 'rescue_detail_screen.dart';

class CropRescueScreen extends StatelessWidget {
  const CropRescueScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isFarmer = auth.isLoggedIn && auth.user?.role == UserRole.farmer;

    return isFarmer ? const _FarmerRescueView() : const _BuyerRescueView();
  }
}

class _BuyerRescueView extends StatefulWidget {
  const _BuyerRescueView();

  @override
  State<_BuyerRescueView> createState() => _BuyerRescueViewState();
}

class _BuyerRescueViewState extends State<_BuyerRescueView> {
  final _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rescue = context.watch<RescueProvider>();
    final listings = rescue.filteredListings;

    return Column(
      children: [

        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _searchController,
                  onChanged: rescue.setSearch,
                  decoration: InputDecoration(
                    hintText: context.t('search_crops'),
                    prefixIcon: const Icon(Icons.search, size: 20),
                    isDense: true,
                    suffixIcon: rescue.searchQuery.isEmpty
                        ? null
                        : IconButton(
                            icon: const Icon(Icons.close, size: 18),
                            onPressed: () {
                              _searchController.clear();
                              rescue.setSearch('');
                            },
                          ),
                  ),
                ),
              ),
              const SizedBox(width: 8),
              _SortButton(current: rescue.sortBy, onPick: rescue.setSort),
            ],
          ),
        ),

        SizedBox(
          height: 40,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 16),
            children: RescueProvider.categories.map((category) {
              final selected = rescue.categoryFilter == category;
              return Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: AutoTranslatedText(
                    '${RescueProvider.categorySymbols[category]}  ${context.t(category == 'all' ? 'all' : category)}',
                    style: const TextStyle(fontSize: 12),
                  ),
                  selected: selected,
                  onSelected: (_) => rescue.setCategory(category),
                  selectedColor: AppTheme.primaryGreen.withValues(alpha: 0.15),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 8),

        Expanded(
          child: listings.isEmpty
              ? SymbolEmptyState(
                  symbol: '🔍',
                  message: context.t('no_rescue_listings'),
                  actionLabel: context.t('clear_filters'),
                  onAction: () {
                    _searchController.clear();
                    rescue.clearFilters();
                  },
                )
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),
                  itemCount: listings.length,
                  itemBuilder: (_, i) => _RescueCard(listing: listings[i]),
                ),
        ),
      ],
    );
  }
}

class _RescueCard extends StatelessWidget {
  final RescueListing listing;

  const _RescueCard({required this.listing});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => Navigator.of(context).push<void>(
        MaterialPageRoute(builder: (_) => RescueDetailScreen(listingId: listing.id)),
      ),
      borderRadius: BorderRadius.circular(18),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppTheme.borderLight),
        ),
        child: Row(
          children: [
            Container(
              width: 64,
              height: 64,
              alignment: Alignment.center,
              decoration: BoxDecoration(
                color: const Color(0xFFF3F4F6),
                borderRadius: BorderRadius.circular(16),
              ),
              child: AutoTranslatedText(listing.emoji, style: const TextStyle(fontSize: 32)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  AutoTranslatedText(
                    listing.cropName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 3),
                  AutoTranslatedText(
                    '📦 ${listing.remainingQuantity.round()} ${listing.unit}   📍 ${listing.location.split(',').first}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11.5, color: AppTheme.textMuted),
                  ),
                  AutoTranslatedText(
                    '👨‍🌾 ${listing.farmerName}   ${listing.urgencySymbol} ${context.tf('days_left', ['${listing.daysLeft}'])}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 11.5, color: AppTheme.textMuted),
                  ),
                  CropMediaGallery(cropId: listing.id),
                  CropMediaUploader(cropId: listing.id, cropName: listing.cropName, farmerName: listing.farmerName),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                AutoTranslatedText(
                  '₹${listing.pricePerUnit.round()}',
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                    color: AppTheme.primaryGreen,
                  ),
                ),
                AutoTranslatedText(
                  '/${listing.unit}',
                  style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                ),
                const SizedBox(height: 6),
                SizedBox(
                  height: 32,
                  child: ElevatedButton(
                    onPressed: () => Navigator.of(context).push<void>(
                      MaterialPageRoute(
                        builder: (_) => RescueDetailScreen(listingId: listing.id),
                      ),
                    ),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 16),
                    ),
                    child: AutoTranslatedText(context.t('buy'), style: const TextStyle(fontSize: 12)),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _SortButton extends StatelessWidget {
  final String current;
  final void Function(String) onPick;

  const _SortButton({required this.current, required this.onPick});

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<String>(
      tooltip: context.t('sort'),
      initialValue: current,
      onSelected: onPick,
      icon: const Icon(Icons.swap_vert, size: 22),
      itemBuilder: (_) => [
        PopupMenuItem(value: 'urgent', child: AutoTranslatedText('⏳  ${context.t('sort_urgent')}')),
        PopupMenuItem(value: 'price_low', child: AutoTranslatedText('⬇️  ${context.t('sort_price_low')}')),
        PopupMenuItem(value: 'price_high', child: AutoTranslatedText('⬆️  ${context.t('sort_price_high')}')),
        PopupMenuItem(value: 'newest', child: AutoTranslatedText('🆕  ${context.t('sort_newest')}')),
      ],
    );
  }
}

class _FarmerRescueView extends StatelessWidget {
  const _FarmerRescueView();

  @override
  Widget build(BuildContext context) {
    final rescue = context.watch<RescueProvider>();
    final auth = context.watch<AuthProvider>();
    final farmerId = auth.user?.id ?? '';
    final myListings = rescue.listingsForFarmer(farmerId);

    final activeCount = myListings.where((l) => l.status == 'active').length;
    final soldCount = myListings.fold<int>(0, (sum, l) => sum + l.orderCount);
    final earnings = rescue.earningsForFarmer(farmerId);

    return Stack(
      children: [
        ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 96),
          children: [
            Row(
              children: [
                Expanded(
                  child: SymbolStat(
                    symbol: '🟢',
                    value: '$activeCount',
                    caption: context.t('live_lots'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SymbolStat(
                    symbol: '📦',
                    value: '$soldCount',
                    caption: context.t('orders'),
                    color: AppTheme.accentTeal,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SymbolStat(
                    symbol: '💰',
                    value: formatRupeesShort(earnings),
                    caption: context.t('earnings'),
                    color: AppTheme.accentAmber,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),
            SectionHeader(symbol: '🚨', title: context.t('my_rescue_lots')),
            if (myListings.isEmpty)
              SymbolEmptyState(
                symbol: '🌾',
                message: context.t('no_rescue_lots_yet'),
                actionLabel: context.t('publish_crop'),
                onAction: () => openPublishRescueSheet(context),
              )
            else
              ...myListings.map((l) => _FarmerLotCard(listing: l)),
          ],
        ),
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton.extended(
            onPressed: () => openPublishRescueSheet(context),
            backgroundColor: AppTheme.primaryGreen,
            foregroundColor: Colors.white,
            icon: const Icon(Icons.add),
            label: AutoTranslatedText(
              context.t('publish_crop'),
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
        ),
      ],
    );
  }
}

class _FarmerLotCard extends StatelessWidget {
  final RescueListing listing;

  const _FarmerLotCard({required this.listing});

  @override
  Widget build(BuildContext context) {
    final rescue = context.read<RescueProvider>();
    final soldPercent =
        listing.quantity == 0 ? 0.0 : (listing.soldQuantity / listing.quantity).clamp(0.0, 1.0);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
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
            children: [
              AutoTranslatedText(listing.emoji, style: const TextStyle(fontSize: 28)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      listing.cropName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
                    ),
                    AutoTranslatedText(
                      '📍 ${listing.location.split(',').first}   📅 ${_formatDate(listing.sellBy)}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              AutoTranslatedText(
                '₹${listing.pricePerUnit.round()}/${listing.unit}',
                style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w900),
              ),
            ],
          ),
          const SizedBox(height: 12),

          ClipRRect(
            borderRadius: BorderRadius.circular(6),
            child: LinearProgressIndicator(
              value: soldPercent.toDouble(),
              minHeight: 6,
              backgroundColor: const Color(0xFFF3F4F6),
              valueColor: const AlwaysStoppedAnimation<Color>(AppTheme.primaryGreen),
            ),
          ),
          const SizedBox(height: 6),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              AutoTranslatedText(
                '✅ ${context.t('sold')} ${listing.soldQuantity.round()} ${listing.unit}',
                style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
              ),
              AutoTranslatedText(
                '📦 ${context.t('remaining')} ${listing.remainingQuantity.round()} ${listing.unit}',
                style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
              ),
            ],
          ),
          const Divider(height: 20),

          Row(
            children: [
              _action(
                icon: Icons.edit_outlined,
                tooltip: context.t('edit'),
                onTap: () => openPublishRescueSheet(context, existing: listing),
              ),
              _action(
                icon: listing.status == 'paused'
                    ? Icons.play_arrow_outlined
                    : Icons.pause_outlined,
                tooltip: context.t(listing.status == 'paused' ? 'resume' : 'pause'),
                onTap: () => rescue.togglePause(listing.id),
              ),
              _action(
                icon: Icons.delete_outline,
                tooltip: context.t('delete'),
                onTap: () => _confirmDelete(context, rescue),
              ),
              const Spacer(),
              StatusPill(
                symbol: listing.statusSymbol,
                label: context.t(
                  listing.status == 'paused'
                      ? 'paused'
                      : listing.status == 'sold_out'
                          ? 'sold_out'
                          : 'live',
                ),
                color: listing.status == 'sold_out'
                    ? AppTheme.accentTeal
                    : listing.status == 'paused'
                        ? AppTheme.textMuted
                        : AppTheme.primaryGreen,
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _confirmDelete(BuildContext context, RescueProvider rescue) {
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: AutoTranslatedText(context.t('delete_listing')),
        content: AutoTranslatedText(context.t('delete_listing_confirm')),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: AutoTranslatedText(context.t('cancel')),
          ),
          ElevatedButton(
            onPressed: () {
              rescue.deleteListing(listing.id);
              Navigator.of(dialogContext).pop();
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppTheme.alertRed),
            child: AutoTranslatedText(context.t('delete')),
          ),
        ],
      ),
    );
  }

  Widget _action({
    required IconData icon,
    required String tooltip,
    required VoidCallback onTap,
  }) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          width: 40,
          height: 36,
          margin: const EdgeInsets.only(right: 8),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: const Color(0xFFF9FAFB),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppTheme.borderLight),
          ),
          child: Icon(icon, size: 18, color: AppTheme.textDark),
        ),
      ),
    );
  }

  static String _formatDate(DateTime date) {
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    return '${date.day} ${months[date.month - 1]}';
  }
}
