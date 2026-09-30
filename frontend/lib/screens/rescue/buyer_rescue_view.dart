import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../localization/l10n_extension.dart';
import '../../models/rescue_listing_model.dart';
import '../../providers/rescue_provider.dart';
import '../../widgets/auto_translated_text.dart';
import '../../widgets/crop_media_uploader.dart';
import '../../widgets/symbol_widgets.dart';
import 'rescue_listing_detail_screen.dart';

// Buyer side of Rescue: browse crops farmers want to clear fast.
// DEMO DATA: there is no backend for buying rescued crops yet (Crop Rescue itself is farmer-only).

class BuyerRescueView extends StatefulWidget {
  const BuyerRescueView({super.key});

  @override
  State<BuyerRescueView> createState() => BuyerRescueViewState();
}

class BuyerRescueViewState extends State<BuyerRescueView> {
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
        MaterialPageRoute(builder: (_) => RescueListingDetailScreen(listingId: listing.id)),
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
                        builder: (_) => RescueListingDetailScreen(listingId: listing.id),
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

