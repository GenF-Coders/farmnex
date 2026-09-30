import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../providers/rescue_provider.dart';
import '../../widgets/auto_translated_text.dart';

/// Opens the "register a harvested lot" sheet.
void openPublishRescueSheet(BuildContext context) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.white,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
    ),
    builder: (_) => const PublishRescueSheet(),
  );
}

class PublishRescueSheet extends StatefulWidget {
  const PublishRescueSheet({super.key});

  @override
  State<PublishRescueSheet> createState() => _PublishRescueSheetState();
}

class _PublishRescueSheetState extends State<PublishRescueSheet> {
  final _quantityController = TextEditingController();
  final _priceController = TextEditingController();

  String? _cropCode;
  String _storage = 'ambient';
  DateTime _harvestedAt = DateTime.now();

  @override
  void initState() {
    super.initState();
    final rescue = context.read<RescueProvider>();
    rescue.clearError();
    if (rescue.crops.isEmpty) rescue.load();
  }

  @override
  void dispose() {
    _quantityController.dispose();
    _priceController.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final date = await showDatePicker(
      context: context,
      initialDate: _harvestedAt,
      firstDate: now.subtract(const Duration(days: 30)),
      lastDate: now,
    );
    if (date != null) setState(() => _harvestedAt = date);
  }

  Future<void> _submit() async {
    final rescue = context.read<RescueProvider>();
    final lot = await rescue.registerLot(
      cropCode: _cropCode ?? '',
      quantityKg: double.tryParse(_quantityController.text.trim()) ?? 0,
      harvestedAt: _harvestedAt,
      storageMode: _storage,
      floorPricePerKg: double.tryParse(_priceController.text.trim()) ?? 0,
    );
    if (!mounted || lot == null) return;
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: AutoTranslatedText('Lot registered. We will warn you before it spoils.'),
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
            Row(children: [
              const AutoTranslatedText('🚨', style: TextStyle(fontSize: 22)),
              const SizedBox(width: 10),
              const Expanded(
                child: AutoTranslatedText(
                  'Register a harvested lot',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
                ),
              ),
              IconButton(icon: const Icon(Icons.close), onPressed: () => Navigator.of(context).pop()),
            ]),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              initialValue: _cropCode,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Crop'),
              items: rescue.crops
                  .map((c) => DropdownMenuItem(value: c.code, child: AutoTranslatedText(c.nameEn)))
                  .toList(),
              onChanged: (v) => setState(() => _cropCode = v),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _quantityController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Quantity (kg)'),
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
                child: Row(children: [
                  const Icon(Icons.event, size: 20, color: AppTheme.textMuted),
                  const SizedBox(width: 10),
                  const Expanded(
                    child: AutoTranslatedText(
                      'Harvested on',
                      style: TextStyle(fontSize: 13, color: AppTheme.textMuted),
                    ),
                  ),
                  AutoTranslatedText(
                    '${_harvestedAt.day}/${_harvestedAt.month}/${_harvestedAt.year}',
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800),
                  ),
                ]),
              ),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _storage,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Storage'),
              items: const [
                DropdownMenuItem(value: 'ambient', child: AutoTranslatedText('Normal (room temperature)')),
                DropdownMenuItem(value: 'cold', child: AutoTranslatedText('Cold storage')),
              ],
              onChanged: (v) => setState(() => _storage = v ?? _storage),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _priceController,
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(
                labelText: 'Lowest price you accept (₹/kg, optional)',
                prefixText: '₹ ',
              ),
            ),
            if (rescue.errorMessage != null) ...[
              const SizedBox(height: 12),
              AutoTranslatedText(
                rescue.errorMessage!,
                style: const TextStyle(fontSize: 12, color: AppTheme.alertRed),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              height: 50,
              child: ElevatedButton(
                onPressed: rescue.isSaving ? null : _submit,
                child: rescue.isSaving
                    ? const SizedBox(
                        width: 22,
                        height: 22,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const AutoTranslatedText(
                        'Register lot',
                        style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900),
                      ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
