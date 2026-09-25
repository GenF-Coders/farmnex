import '../auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:provider/provider.dart';
import '../../core/guards/auth_guard.dart';
import '../../core/theme/app_theme.dart';
import '../../providers/auth_provider.dart';
import '../../providers/waste_provider.dart';
import '../../providers/crop_media_provider.dart';

class WasteToWealthDialog extends StatefulWidget {
  const WasteToWealthDialog({super.key});

  @override
  State<WasteToWealthDialog> createState() => _WasteToWealthDialogState();
}

class _WasteToWealthDialogState extends State<WasteToWealthDialog> {
  String _selectedWasteType = 'Paddy Straw (धान की पराली)';
  final _quantityController = TextEditingController(text: '10 Tonnes');
  final _locationController = TextEditingController(text: 'Indore, Madhya Pradesh');
  PlatformFile? _mediaFile;
  bool _showSuccess = false;

  bool get _hasPhotoAttached => _mediaFile != null;

  final List<String> _wasteTypes = const [
    'Paddy Straw (धान की पराली)',
    'Sugarcane Bagasse (गन्ने की खोई)',
    'Corn Stalks (मक्के का डंठल)',
    'Cotton Stalks (कपास की लकड़ी)',
    'Fruit & Vegetable Pulp (फलों का गूदा)',
  ];

  @override
  void dispose() {
    _quantityController.dispose();
    _locationController.dispose();
    super.dispose();
  }

  Future<void> _pickMedia() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['jpg', 'jpeg', 'png', 'webp', 'mp4', 'mov', 'm4v', 'avi', 'webm'],
      withData: true,
    );
    if (result != null && result.files.isNotEmpty && mounted) {
      setState(() => _mediaFile = result.files.first);
    }
  }

  void _submitListing() {
    final auth = context.read<AuthProvider>();
    final waste = context.read<WasteProvider>();

    AuthGuard.requireAuth(
      context: context,
      authProvider: auth,
      actionType: 'waste',
      actionReason: 'Please sign in to list crop residue and connect with bio-fuel buyers',
      onAuthenticated: () async {
        final success = await waste.createWasteListing(
          farmerName: auth.user?.name ?? 'Verified Farmer',
          wasteType: _selectedWasteType,
          quantity: _quantityController.text.trim(),
          location: _locationController.text.trim(),
          bestUse: 'Bio-CNG & Compressed Thermal Pellets',
          potentialIncome: '₹14,000 (@ ₹1,400/T)',
          mediaPath: _mediaFile?.path,
        );

        if (_mediaFile != null) {
          context.read<CropMediaProvider>().addFiles(
            cropId: 'waste:${_selectedWasteType}',
            cropName: _selectedWasteType,
            farmerName: auth.user?.name ?? 'Farmer',
            files: [_mediaFile!],
          );
        }

        if (success && mounted) {
          setState(() => _showSuccess = true);
          Future.delayed(const Duration(seconds: 3), () {
            if (mounted) setState(() => _showSuccess = false);
          });
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final waste = context.watch<WasteProvider>();

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      backgroundColor: Colors.white,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 540, maxHeight: 720),
        child: Column(
          children: [

            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              decoration: const BoxDecoration(
                color: AppTheme.primaryGreen,
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.recycling, color: Colors.white, size: 22),
                  ),
                  const SizedBox(width: 12),
                  const Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AutoTranslatedText(
                          'Waste to Wealth (कचरे से कमाई)',
                          style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w800),
                        ),
                        AutoTranslatedText(
                          'Monetize stubble, husk & organic biomass',
                          style: TextStyle(color: Color(0xFFDCFCE7), fontSize: 11),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.white),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [

                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFFFEF3C7),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(color: const Color(0xFFFDE68A)),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.eco, color: Color(0xFFD97706), size: 20),
                        SizedBox(width: 10),
                        Expanded(
                          child: AutoTranslatedText(
                            'Don’t burn stubble! Bio-CNG and pellet manufacturing plants buy agricultural waste directly from your farm.',
                            style: TextStyle(fontSize: 11.5, color: Color(0xFF78350F), fontWeight: FontWeight.w600),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  if (_showSuccess)
                    Container(
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 16),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryGreen,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Row(
                        children: [
                          Icon(Icons.check_circle, color: Colors.white, size: 20),
                          SizedBox(width: 8),
                          Expanded(
                            child: AutoTranslatedText(
                              'Listing created! 3 Biofuel processing units within 45km notified.',
                              style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                    ),

                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF9FAFB),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.borderLight),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AutoTranslatedText(
                          'LIST NEW BIOMASS / RESIDUE',
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.textMuted, letterSpacing: 0.5),
                        ),
                        const SizedBox(height: 12),

                        DropdownButtonFormField<String>(
                          initialValue: _selectedWasteType,
                          decoration: const InputDecoration(labelText: 'Residue Type'),
                          items: _wasteTypes.map((type) => DropdownMenuItem(value: type, child: AutoTranslatedText(type, style: const TextStyle(fontSize: 13)))).toList(),
                          onChanged: (val) => setState(() => _selectedWasteType = val!),
                        ),
                        const SizedBox(height: 12),

                        Row(
                          children: [
                            Expanded(
                              child: TextFormField(
                                controller: _quantityController,
                                decoration: const InputDecoration(labelText: 'Quantity (e.g. 10 Tonnes)'),
                              ),
                            ),
                            const SizedBox(width: 10),
                            Expanded(
                              child: TextFormField(
                                controller: _locationController,
                                decoration: const InputDecoration(labelText: 'Mandi / Village Location'),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),

                        InkWell(
                          onTap: _pickMedia,
                          borderRadius: BorderRadius.circular(12),
                          child: Container(
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                            decoration: BoxDecoration(
                              color: _hasPhotoAttached ? AppTheme.primaryGreen.withValues(alpha: 0.08) : Colors.white,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: _hasPhotoAttached ? AppTheme.primaryGreen : AppTheme.borderLight,
                              ),
                            ),
                            child: Row(
                              children: [
                                Icon(
                                  _mediaFile != null ? Icons.check_circle : Icons.camera_alt_outlined,
                                  color: _mediaFile != null ? AppTheme.primaryGreen : AppTheme.textMuted,
                                  size: 20,
                                ),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: AutoTranslatedText(
                                    _mediaFile != null ? _mediaFile!.name : 'Attach farm photo / video for quality check',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: _mediaFile != null ? FontWeight.bold : FontWeight.w500,
                                      color: _mediaFile != null ? AppTheme.primaryGreen : AppTheme.textDark,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),

                        ElevatedButton(
                          onPressed: waste.isListing ? null : _submitListing,
                          child: waste.isListing
                              ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                              : AutoTranslatedText('Publish Biomass Listing (बिक्री हेतु लिस्ट करें)'),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  AutoTranslatedText('Available Residue Lots in Your APMC Circle', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 10),

                  ...waste.items.map((item) => Container(
                        margin: const EdgeInsets.only(bottom: 10),
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(color: AppTheme.borderLight),
                        ),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: const Color(0xFFF0FDF4),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Icon(Icons.grass, color: AppTheme.primaryGreen, size: 22),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  AutoTranslatedText(item.wasteType, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                                  const SizedBox(height: 2),
                                  AutoTranslatedText('${item.quantity} • ${item.location} • By ${item.farmerName}', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                                  const SizedBox(height: 6),
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: const Color(0xFFECFDF5),
                                          borderRadius: BorderRadius.circular(6),
                                        ),
                                        child: AutoTranslatedText(item.bestUse, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                                      ),
                                      AutoTranslatedText(item.potentialIncome, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: Color(0xFF166534))),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      )),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
