import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/network/listing_api.dart';
import '../../core/theme/app_theme.dart';
import '../../models/crop_model.dart';
import '../../models/listing_model.dart';
import '../../providers/listing_provider.dart';
import '../../widgets/symbol_widgets.dart';

class MyCropsScreen extends StatefulWidget {
  const MyCropsScreen({super.key});

  @override
  State<MyCropsScreen> createState() => _MyCropsScreenState();
}

class _MyCropsScreenState extends State<MyCropsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) context.read<ListingProvider>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final listings = context.watch<ListingProvider>();

    return Stack(
      children: [
        RefreshIndicator(
          onRefresh: () => context.read<ListingProvider>().load(),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
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
                      symbol: '📋',
                      value: '${listings.listings.length}',
                      caption: 'All lots',
                      color: AppTheme.accentTeal,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              SymbolStat(
                symbol: '💰',
                value: formatRupees(listings.inventoryValue),
                caption: 'Value of live lots at your prices',
              ),
              const SizedBox(height: 20),
              const SectionHeader(symbol: '📋', title: 'My lots'),
              if (listings.isLoading && listings.listings.isEmpty)
                const Padding(padding: EdgeInsets.all(28), child: Center(child: CircularProgressIndicator()))
              else if (listings.error != null && listings.listings.isEmpty)
                Column(children: [
                  SymbolEmptyState(symbol: '☁️', message: listings.error!),
                  OutlinedButton(
                    onPressed: () => context.read<ListingProvider>().load(),
                    child: const AutoTranslatedText('Try again'),
                  ),
                ])
              else if (listings.listings.isEmpty)
                const SymbolEmptyState(symbol: '🌱', message: 'No lots listed yet.')
              else
                ...listings.listings.map((crop) => _ListingTile(crop: crop)),
            ],
          ),
        ),
        Positioned(
          right: 16,
          bottom: 16,
          child: FloatingActionButton.extended(
            onPressed: () => _openAddSheet(context),
            backgroundColor: AppTheme.primaryGreen,
            foregroundColor: Colors.white,
            icon: const AutoTranslatedText('➕', style: TextStyle(fontSize: 16)),
            label: const AutoTranslatedText('🌾  List lot', style: TextStyle(fontWeight: FontWeight.w800)),
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
    final (statusSymbol, statusLabel, statusColor) = switch (crop.status) {
      'active' => ('🟢', 'Live', AppTheme.primaryGreen),
      'closed' => ('⚪', 'Closed', AppTheme.textMuted),
      'sold_out' => ('✅', 'Sold', AppTheme.accentTeal),
      _ => ('⚪', 'Draft', AppTheme.textMuted),
    };
    final closed = crop.status == 'closed';

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
                      '${crop.biddingActive ? '⚖️ Pre-bid' : '🛒 Fixed price'}'
                      '${crop.variety.isEmpty ? '' : '  •  🏅 ${crop.variety}'}',
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
              Expanded(child: _metric('💰', '₹${crop.currentPrice.round()}', '/${crop.unit}')),
              Expanded(child: _metric('⚖️', '${crop.quantityAvailable}', '${crop.unit} left')),
            ],
          ),
          if (!closed) ...[
            const Divider(height: 20),
            Row(
              children: [
                _iconAction(
                  symbol: '₹',
                  tooltip: 'Set selling price',
                  onTap: () => _editPrice(context, crop),
                ),
                _iconAction(
                  symbol: '🗑️',
                  tooltip: 'Close lot',
                  onTap: () => _closeLot(context, crop),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _closeLot(BuildContext context, CropItem crop) async {
    final messenger = ScaffoldMessenger.of(context);
    final error = await context.read<ListingProvider>().remove(crop.id);
    if (error != null) {
      messenger.showSnackBar(SnackBar(content: AutoTranslatedText('⚠️ $error')));
    }
  }

  void _editPrice(BuildContext context, CropItem crop) {
    final controller = TextEditingController(text: crop.currentPrice.toStringAsFixed(0));
    final messenger = ScaffoldMessenger.of(context);
    final listings = context.read<ListingProvider>();
    showDialog<void>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: AutoTranslatedText('Set price • ${crop.name}', style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
        content: TextField(
          controller: controller,
          autofocus: true,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(labelText: 'Selling price per ${crop.unit}', prefixText: '₹ '),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const AutoTranslatedText('Cancel')),
          ElevatedButton(
            style: ElevatedButton.styleFrom(minimumSize: const Size(0, 48)),
            onPressed: () async {
              final price = double.tryParse(controller.text.trim());
              if (price == null || price <= 0) return;
              Navigator.pop(dialogContext);
              final error = await listings.updatePrice(crop.id, price);
              if (error != null) {
                messenger.showSnackBar(SnackBar(content: AutoTranslatedText('⚠️ $error')));
              }
            },
            child: const AutoTranslatedText('Save price'),
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
  final _priceController = TextEditingController();
  final _quantityController = TextEditingController();
  // New-farm form (only shown when the farmer has no farm yet).
  final _farmName = TextEditingController();
  final _address = TextEditingController();
  final _city = TextEditingController();
  final _district = TextEditingController();
  final _state = TextEditingController();
  final _postal = TextEditingController();

  bool _loading = true;
  bool _saving = false;
  String? _error;
  List<CropTypeModel> _cropTypes = [];
  List<FarmSummary> _farms = [];
  CropTypeModel? _cropType;
  String _grade = 'Grade A';
  bool _organic = false;
  bool _preBid = false;

  @override
  void initState() {
    super.initState();
    _loadSetup();
  }

  @override
  void dispose() {
    for (final c in [_priceController, _quantityController, _farmName, _address, _city, _district, _state, _postal]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _loadSetup() async {
    final listings = context.read<ListingProvider>();
    try {
      final types = await listings.cropTypes();
      final farms = await listings.myFarms();
      if (!mounted) return;
      setState(() {
        _cropTypes = types;
        _farms = farms;
        _cropType = types.isEmpty ? null : types.first;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = listingErrorMessage(e);
        _loading = false;
      });
    }
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: AutoTranslatedText(message)));
  }

  Future<void> _submit() async {
    final cropType = _cropType;
    final price = double.tryParse(_priceController.text.trim()) ?? 0;
    final quantity = double.tryParse(_quantityController.text.trim()) ?? 0;
    if (cropType == null || price <= 0 || quantity <= 0) {
      _showMessage('⚠️ Choose a crop and fill ₹ price and ⚖️ quantity.');
      return;
    }
    if (_farms.isEmpty &&
        [_farmName, _address, _city, _district, _state, _postal].any((c) => c.text.trim().isEmpty)) {
      _showMessage('⚠️ Fill in all the farm details.');
      return;
    }

    final listings = context.read<ListingProvider>();
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    setState(() => _saving = true);
    try {
      var farm = _farms.isEmpty ? null : _farms.first;
      farm ??= await listings.createFarm(
        farmName: _farmName.text.trim(),
        addressLine1: _address.text.trim(),
        city: _city.text.trim(),
        district: _district.text.trim(),
        state: _state.text.trim(),
        postalCode: _postal.text.trim(),
      );
      // Remember the new farm so a retry doesn't create a second one.
      if (_farms.isEmpty) _farms = [farm];
      final error = await listings.addListing(
        farmId: farm.publicId,
        cropType: cropType,
        price: price,
        quantity: quantity,
        grade: _grade,
        preBid: _preBid,
        isOrganic: _organic,
      );
      if (error != null) {
        if (mounted) setState(() => _saving = false);
        messenger.showSnackBar(SnackBar(content: AutoTranslatedText('⚠️ $error')));
        return;
      }
      navigator.pop();
      messenger.showSnackBar(
        const SnackBar(
          content: AutoTranslatedText('✅ Lot is live.'),
          backgroundColor: AppTheme.primaryGreen,
        ),
      );
    } catch (e) {
      if (mounted) setState(() => _saving = false);
      messenger.showSnackBar(SnackBar(content: AutoTranslatedText('⚠️ ${listingErrorMessage(e)}')));
    }
  }

  Widget _field(TextEditingController c, String label, {TextInputType? type}) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: TextField(controller: c, keyboardType: type, decoration: InputDecoration(labelText: label)),
      );

  @override
  Widget build(BuildContext context) {
    final unit = _cropType?.defaultUnit ?? 'unit';
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
            if (_loading)
              const Padding(padding: EdgeInsets.all(24), child: Center(child: CircularProgressIndicator()))
            else if (_error != null)
              Column(children: [
                AutoTranslatedText(_error!, textAlign: TextAlign.center),
                const SizedBox(height: 10),
                OutlinedButton(
                  onPressed: () {
                    setState(() {
                      _loading = true;
                      _error = null;
                    });
                    _loadSetup();
                  },
                  child: const AutoTranslatedText('Try again'),
                ),
              ])
            else ...[
              const AutoTranslatedText('Crop', style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _cropTypes.map((type) {
                  final selected = _cropType?.publicId == type.publicId;
                  return ChoiceChip(
                    label: AutoTranslatedText('${type.emoji} ${type.name}', style: const TextStyle(fontSize: 12)),
                    selected: selected,
                    onSelected: (_) => setState(() => _cropType = type),
                    selectedColor: AppTheme.primaryGreen.withValues(alpha: 0.15),
                  );
                }).toList(),
              ),
              const SizedBox(height: 14),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _priceController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(labelText: '💰  ₹ / $unit'),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: TextField(
                      controller: _quantityController,
                      keyboardType: TextInputType.number,
                      decoration: InputDecoration(labelText: '⚖️  Quantity ($unit)'),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  const AutoTranslatedText('🏅', style: TextStyle(fontSize: 16)),
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
                  const AutoTranslatedText('🌿', style: TextStyle(fontSize: 16)),
                  Switch(value: _organic, onChanged: (v) => setState(() => _organic = v)),
                ],
              ),
              Row(
                children: [
                  const Expanded(child: AutoTranslatedText('⚖️  Accept pre-bids from buyers', style: TextStyle(fontSize: 12.5))),
                  Switch(value: _preBid, onChanged: (v) => setState(() => _preBid = v)),
                ],
              ),
              if (_farms.isEmpty) ...[
                const Divider(height: 24),
                const AutoTranslatedText('🏡  Your farm (one-time)', style: TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800)),
                const SizedBox(height: 8),
                _field(_farmName, 'Farm name'),
                _field(_address, 'Address'),
                _field(_city, 'Village / city'),
                _field(_district, 'District'),
                _field(_state, 'State'),
                _field(_postal, 'PIN code', type: TextInputType.number),
              ],
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: _saving ? null : _submit,
                child: _saving
                    ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
                    : const AutoTranslatedText('✅  Submit lot'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
