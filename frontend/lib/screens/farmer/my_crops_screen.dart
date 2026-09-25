import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/crop_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/listing_provider.dart';
import '../../widgets/symbol_widgets.dart';
import '../../widgets/crop_media_uploader.dart';

class MyCropsScreen extends StatelessWidget {
  const MyCropsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final listings = context.watch<ListingProvider>();

    return Stack(
      children: [
        ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
          children: [
            Row(
              children: [
                Expanded(
                  child: SymbolStat(
                    symbol: '🌾',
                    value: '${listings.activeListings.length}',
                    caption: 'Live lots',
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SymbolStat(
                    symbol: '👁️',
                    value: '${listings.totalViews}',
                    caption: 'Views',
                    color: AppTheme.accentTeal,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SymbolStat(
                    symbol: '⚖️',
                    value: '${listings.totalBids}',
                    caption: 'Bids',
                    color: AppTheme.accentAmber,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            SymbolStat(
              symbol: '💰',
              value: formatRupees(listings.inventoryValue),
              caption: 'Inventory value at today\'s mandi rate',
            ),
            const SizedBox(height: 20),
            const SectionHeader(symbol: '📋', title: 'My lots'),
            if (listings.listings.isEmpty)
              const SymbolEmptyState(symbol: '🌱', message: 'No lots listed yet.')
            else
              ...listings.listings.map((crop) => _ListingTile(crop: crop)),
          ],
        ),
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton.extended(
            onPressed: () => _openAddSheet(context),
            backgroundColor: AppTheme.primaryGreen,
            foregroundColor: Colors.white,
            icon: AutoTranslatedText('➕', style: TextStyle(fontSize: 16)),
            label: AutoTranslatedText('🌾  List lot', style: TextStyle(fontWeight: FontWeight.w800)),
          ),
        ),
      ],
    );
  }

  void _openAddSheet(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => const _AddLotSheet(),
    );
  }
}

class _ListingTile extends StatelessWidget {
  final CropItem crop;

  const _ListingTile({required this.crop});

  @override
  Widget build(BuildContext context) {
    final listings = context.read<ListingProvider>();
    final (statusSymbol, statusLabel, statusColor) = switch (crop.status) {
      'active' => ('🟢', 'Live', AppTheme.primaryGreen),
      'paused' => ('⏸️', 'Paused', AppTheme.textMuted),
      'sold_out' => ('✅', 'Sold', AppTheme.accentTeal),
      'pending_approval' => ('⏳', 'Review', AppTheme.accentAmber),
      _ => ('⚪', 'Draft', AppTheme.textMuted),
    };

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
              AutoTranslatedText(crop.emoji, style: const TextStyle(fontSize: 26)),
              const SizedBox(width: 10),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    AutoTranslatedText(
                      crop.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w800),
                    ),
                    AutoTranslatedText(
                      '🏅 ${crop.grade}${crop.isOrganic ? '  •  🌿 Organic' : ''}  •  📍 ${crop.location}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                    ),
                  ],
                ),
              ),
              StatusPill(symbol: statusSymbol, label: statusLabel, color: statusColor),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              Expanded(child: _metric('💰', '₹${crop.currentPrice.round()}', '/q')),
              Expanded(child: _metric('⚖️', '${crop.quantityAvailable}', 'q left')),
              Expanded(child: _metric('👁️', '${crop.views}', 'views')),
              Expanded(child: _metric('⚖️', '${crop.bidsCount}', 'bids')),
              Expanded(
                child: _metric(
                  crop.priceTrend >= 0 ? '📈' : '📉',
                  '${crop.priceTrend >= 0 ? '+' : ''}${crop.priceTrend.toStringAsFixed(1)}%',
                  'trend',
                ),
              ),
            ],
          ),
          CropMediaGallery(cropId: crop.id),
          const Divider(height: 20),
          Row(
            children: [
              _iconAction(
                symbol: crop.status == 'paused' ? '▶️' : '⏸️',
                tooltip: crop.status == 'paused' ? 'Resume' : 'Pause',
                onTap: () => listings.togglePause(crop.id),
              ),
              Expanded(
                child: CropMediaUploader(cropId: crop.id, cropName: crop.name),
              ),
              _iconAction(
                symbol: '₹',
                tooltip: 'Set selling price',
                onTap: () => _editPrice(context, crop),
              ),
              _iconAction(
                symbol: '📊',
                tooltip: 'Analytics',
                onTap: () => ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: AutoTranslatedText('📊 ${crop.views} views • ${crop.bidsCount} bids • ⭐ ${crop.rating}')),
                ),
              ),
              _iconAction(
                symbol: '🗑️',
                tooltip: 'Delete',
                onTap: () => listings.remove(crop.id),
              ),
              const SizedBox(width: 8),
              AutoTranslatedText(
                '⭐ ${crop.rating}  (${crop.ratingCount})',
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppTheme.textMuted),
              ),
            ],
          ),
        ],
      ),
    );
  }

  void _editPrice(BuildContext context, CropItem crop) {
    final controller = TextEditingController(text: crop.currentPrice.toStringAsFixed(0));
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: AutoTranslatedText('Set price • ${crop.name}', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
        content: TextField(
          controller: controller,
          autofocus: true,
          keyboardType: TextInputType.number,
          decoration: const InputDecoration(labelText: 'Selling price per quintal', prefixText: '₹ '),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: AutoTranslatedText('Cancel')),
          ElevatedButton(
            onPressed: () {
              final price = double.tryParse(controller.text.trim());
              if (price == null || price <= 0) return;
              context.read<ListingProvider>().updatePrice(crop.id, price);
              Navigator.pop(dialogContext);
            },
            child: AutoTranslatedText('Save price'),
          ),
        ],
      ),
    ).then((_) => controller.dispose());
  }

  Widget _metric(String symbol, String value, String caption) {
    return Column(
      children: [
        AutoTranslatedText(symbol, style: const TextStyle(fontSize: 13)),
        const SizedBox(height: 2),
        FittedBox(
          fit: BoxFit.scaleDown,
          child: AutoTranslatedText(value, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w900)),
        ),
        AutoTranslatedText(caption, style: const TextStyle(fontSize: 9, color: AppTheme.textMuted)),
      ],
    );
  }

  Widget _iconAction({
    required String symbol,
    required String tooltip,
    required VoidCallback onTap,
  }) {
    return Tooltip(
      message: tooltip,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(10),
        child: Container(
          width: 36,
          height: 32,
          margin: const EdgeInsets.only(right: 6),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: const Color(0xFFF9FAFB),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: AppTheme.borderLight),
          ),
          child: AutoTranslatedText(symbol, style: const TextStyle(fontSize: 14)),
        ),
      ),
    );
  }
}

class _AddLotSheet extends StatefulWidget {
  const _AddLotSheet();

  @override
  State<_AddLotSheet> createState() => _AddLotSheetState();
}

class _AddLotSheetState extends State<_AddLotSheet> {
  final _nameController = TextEditingController();
  final _priceController = TextEditingController();
  final _quantityController = TextEditingController();

  String _emoji = '🌾';
  String _category = 'Grains';
  String _grade = 'Grade A';
  bool _organic = false;

  static const Map<String, String> _cropSymbols = {
    '🌾': 'Grains',
    '🌱': 'Oilseeds',
    '🧅': 'Vegetables',
    '🍅': 'Vegetables',
    '🥔': 'Vegetables',
    '🍇': 'Fruits',
    '🥭': 'Fruits',
    '🫘': 'Grains',
  };

  @override
  void dispose() {
    _nameController.dispose();
    _priceController.dispose();
    _quantityController.dispose();
    super.dispose();
  }

  void _submit() {
    final name = _nameController.text.trim();
    final price = double.tryParse(_priceController.text.trim()) ?? 0;
    final quantity = int.tryParse(_quantityController.text.trim()) ?? 0;
    if (name.isEmpty || price <= 0 || quantity <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: AutoTranslatedText('⚠️ Fill crop name, ₹ price and ⚖️ quantity.')),
      );
      return;
    }

    final user = context.read<AuthProvider>().user;
    context.read<ListingProvider>().addListing(
          name: name,
          category: _category,
          emoji: _emoji,
          price: price,
          quantity: quantity,
          grade: _grade,
          location: user?.address ?? 'My village',
          farmerName: user?.name ?? 'Farmer',
          isOrganic: _organic,
        );

    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: AutoTranslatedText('✅ Lot submitted. ⏳ APMC review usually takes under 2 hours.'),
        backgroundColor: AppTheme.primaryGreen,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Row(
              children: [
                AutoTranslatedText('🌾', style: TextStyle(fontSize: 22)),
                SizedBox(width: 10),
                AutoTranslatedText('List a new lot', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
              ],
            ),
            const SizedBox(height: 16),

            AutoTranslatedText('Crop symbol', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _cropSymbols.keys.map((symbol) {
                final selected = _emoji == symbol;
                return InkWell(
                  onTap: () => setState(() {
                    _emoji = symbol;
                    _category = _cropSymbols[symbol]!;
                  }),
                  borderRadius: BorderRadius.circular(12),
                  child: Container(
                    width: 46,
                    height: 46,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: selected ? AppTheme.primaryGreen.withValues(alpha: 0.12) : const Color(0xFFF9FAFB),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: selected ? AppTheme.primaryGreen : AppTheme.borderLight,
                        width: selected ? 1.8 : 1,
                      ),
                    ),
                    child: AutoTranslatedText(symbol, style: const TextStyle(fontSize: 22)),
                  ),
                );
              }).toList(),
            ),
            const SizedBox(height: 14),

            TextField(
              controller: _nameController,
              decoration: const InputDecoration(labelText: '🏷️  Crop name', hintText: 'Sharbati Wheat'),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _priceController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: '💰  ₹ / quintal'),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: TextField(
                    controller: _quantityController,
                    keyboardType: TextInputType.number,
                    decoration: const InputDecoration(labelText: '⚖️  Quintals'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                AutoTranslatedText('🏅', style: TextStyle(fontSize: 16)),
                const SizedBox(width: 8),
                ...['Grade A', 'Grade B', 'Grade C'].map(
                  (g) => Padding(
                    padding: const EdgeInsets.only(right: 6),
                    child: ChoiceChip(
                      label: AutoTranslatedText(g.replaceAll('Grade ', ''), style: const TextStyle(fontSize: 12)),
                      selected: _grade == g,
                      onSelected: (_) => setState(() => _grade = g),
                      selectedColor: AppTheme.primaryGreen.withValues(alpha: 0.15),
                    ),
                  ),
                ),
                const Spacer(),
                AutoTranslatedText('🌿', style: TextStyle(fontSize: 16)),
                Switch(
                  value: _organic,
                  onChanged: (v) => setState(() => _organic = v),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ElevatedButton(onPressed: _submit, child: AutoTranslatedText('✅  Submit lot')),
          ],
        ),
      ),
    );
  }
}
