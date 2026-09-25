import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../localization/l10n_extension.dart';
import '../../models/rescue_listing_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/rescue_provider.dart';

void openPublishRescueSheet(BuildContext context, {RescueListing? existing}) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
    ),
    builder: (_) => PublishRescueSheet(existing: existing),
  );
}

class PublishRescueSheet extends StatefulWidget {
  final RescueListing? existing;

  const PublishRescueSheet({super.key, this.existing});

  @override
  State<PublishRescueSheet> createState() => _PublishRescueSheetState();
}

class _PublishRescueSheetState extends State<PublishRescueSheet> {
  late final TextEditingController _nameController;
  late final TextEditingController _quantityController;
  late final TextEditingController _priceController;
  late final TextEditingController _locationController;
  late final TextEditingController _descriptionController;

  String _emoji = '🍅';
  String _category = 'cat_vegetables';
  String _unit = 'kg';
  late DateTime _sellBy;

  static const List<String> _units = ['kg', 'Quintal', 'Crate', 'Ton'];

  static const Map<String, String> _cropCategory = {
    '🍅': 'cat_vegetables',
    '🧅': 'cat_vegetables',
    '🥔': 'cat_vegetables',
    '🌶️': 'cat_vegetables',
    '🥦': 'cat_vegetables',
    '🍌': 'cat_fruits',
    '🍇': 'cat_fruits',
    '🥭': 'cat_fruits',
    '🌾': 'cat_grains',
    '🫘': 'cat_pulses',
  };

  bool get _isEditing => widget.existing != null;

  @override
  void initState() {
    super.initState();
    final e = widget.existing;
    _nameController = TextEditingController(text: e?.cropName ?? '');
    _quantityController =
        TextEditingController(text: e == null ? '' : e.quantity.round().toString());
    _priceController =
        TextEditingController(text: e == null ? '' : e.pricePerUnit.round().toString());
    _locationController = TextEditingController(text: e?.location ?? '');
    _descriptionController = TextEditingController(text: e?.description ?? '');
    _emoji = e?.emoji ?? '🍅';
    _category = e?.category ?? 'cat_vegetables';
    _unit = e?.unit ?? 'kg';
    _sellBy = e?.sellBy ?? DateTime.now().add(const Duration(days: 3));

    if (e == null) {

      final user = context.read<AuthProvider>().user;
      _locationController.text = user?.address ?? '';
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _quantityController.dispose();
    _priceController.dispose();
    _locationController.dispose();
    _descriptionController.dispose();
    super.dispose();
  }

  double get _estimatedTotal {
    final q = double.tryParse(_quantityController.text.trim()) ?? 0;
    final p = double.tryParse(_priceController.text.trim()) ?? 0;
    return q * p;
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _sellBy,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 90)),
    );
    if (picked != null) setState(() => _sellBy = picked);
  }

  Future<void> _submit() async {
    final rescue = context.read<RescueProvider>();
    final user = context.read<AuthProvider>().user;

    final name = _nameController.text.trim();
    final quantity = double.tryParse(_quantityController.text.trim()) ?? 0;
    final price = double.tryParse(_priceController.text.trim()) ?? 0;

    if (name.isEmpty || quantity <= 0 || price <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: AutoTranslatedText(context.t('err_fill_required'))),
      );
      return;
    }

    if (_isEditing) {
      rescue.updateListing(
        widget.existing!.id,
        pricePerUnit: price,
        quantity: quantity,
        sellBy: _sellBy,
        description: _descriptionController.text.trim(),
      );
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: AutoTranslatedText(context.t('listing_updated')),
          backgroundColor: AppTheme.primaryGreen,
        ),
      );
      return;
    }

    final created = await rescue.publish(
      cropName: name,
      category: _category,
      emoji: _emoji,
      quantity: quantity,
      unit: _unit,
      pricePerUnit: price,
      location: _locationController.text.trim(),
      sellBy: _sellBy,
      description: _descriptionController.text.trim(),
      farmerId: user?.id ?? 'guest',
      farmerName: user?.name ?? '',
    );

    if (!mounted) return;
    if (created == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: AutoTranslatedText(context.t(rescue.errorKey ?? 'err_generic'))),
      );
      return;
    }

    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: AutoTranslatedText(context.t('listing_published')),
        backgroundColor: AppTheme.primaryGreen,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final rescue = context.watch<RescueProvider>();

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 18,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                AutoTranslatedText('🚨', style: TextStyle(fontSize: 22)),
                const SizedBox(width: 10),
                Expanded(
                  child: AutoTranslatedText(
                    context.t(_isEditing ? 'edit_listing' : 'publish_crop'),
                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
            const SizedBox(height: 10),

            if (!_isEditing) ...[
              AutoTranslatedText(context.t('choose_crop'),
                  style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: _cropCategory.keys.map((symbol) {
                  final selected = _emoji == symbol;
                  return InkWell(
                    onTap: () => setState(() {
                      _emoji = symbol;
                      _category = _cropCategory[symbol]!;
                    }),
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      width: 48,
                      height: 48,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        color: selected
                            ? AppTheme.primaryGreen.withValues(alpha: 0.12)
                            : const Color(0xFFF9FAFB),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: selected ? AppTheme.primaryGreen : AppTheme.borderLight,
                          width: selected ? 1.8 : 1,
                        ),
                      ),
                      child: AutoTranslatedText(symbol, style: const TextStyle(fontSize: 24)),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 14),
            ],

            TextField(
              controller: _nameController,
              enabled: !_isEditing,
              decoration: InputDecoration(labelText: context.t('crop_name')),
            ),
            const SizedBox(height: 12),

            Row(
              children: [
                Expanded(
                  flex: 2,
                  child: TextField(
                    controller: _quantityController,
                    keyboardType: TextInputType.number,
                    onChanged: (_) => setState(() {}),
                    decoration: InputDecoration(labelText: context.t('quantity')),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    value: _unit,
                    isExpanded: true,
                    decoration: InputDecoration(labelText: context.t('unit')),
                    items: _units
                        .map((u) => DropdownMenuItem(
                              value: u,
                              child: AutoTranslatedText(u, style: const TextStyle(fontSize: 13)),
                            ))
                        .toList(),
                    onChanged: _isEditing ? null : (v) => setState(() => _unit = v ?? _unit),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _priceController,
              keyboardType: TextInputType.number,
              onChanged: (_) => setState(() {}),
              decoration: InputDecoration(
                labelText: '${context.t('your_price')}  (₹/$_unit)',
                prefixText: '₹ ',
              ),
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _locationController,
              decoration: InputDecoration(labelText: context.t('location')),
            ),
            const SizedBox(height: 12),

            InkWell(
              onTap: _pickDate,
              borderRadius: BorderRadius.circular(12),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 15),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.borderLight),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.event, size: 20, color: AppTheme.textMuted),
                    const SizedBox(width: 10),
                    Expanded(
                      child: AutoTranslatedText(
                        context.t('sell_by'),
                        style: const TextStyle(fontSize: 13, color: AppTheme.textMuted),
                      ),
                    ),
                    AutoTranslatedText(
                      '${_sellBy.day}/${_sellBy.month}/${_sellBy.year}',
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            TextField(
              controller: _descriptionController,
              maxLines: 2,
              decoration: InputDecoration(labelText: context.t('short_description')),
            ),
            const SizedBox(height: 16),

            if (_estimatedTotal > 0)
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFF0FDF4),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  children: [
                    AutoTranslatedText('💰', style: TextStyle(fontSize: 18)),
                    const SizedBox(width: 10),
                    Expanded(
                      child: AutoTranslatedText(
                        context.t('lot_value'),
                        style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
                      ),
                    ),
                    AutoTranslatedText(
                      '₹${_estimatedTotal.round()}',
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w900,
                        color: AppTheme.primaryGreen,
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 16),

            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: rescue.isLoading ? null : _submit,
                child: rescue.isLoading
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : AutoTranslatedText(
                        context.t(_isEditing ? 'save_changes' : 'publish'),
                        style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
