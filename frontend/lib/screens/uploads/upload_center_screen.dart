import '../../widgets/auto_translated_text.dart';
import 'package:dio/dio.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/network/backend_service.dart';
import '../../core/theme/app_theme.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';

class UploadCenterScreen extends StatefulWidget {
  const UploadCenterScreen({super.key});

  @override
  State<UploadCenterScreen> createState() => _UploadCenterScreenState();
}

class _UploadCenterScreenState extends State<UploadCenterScreen> {
  final _farmIdController = TextEditingController();
  final _backend = BackendService();
  PlatformFile? _selectedFile;
  bool _uploading = false;
  String? _message;
  final List<PlatformFile> _documents = [];

  @override
  void dispose() {
    _farmIdController.dispose();
    super.dispose();
  }

  UserRole get _role => context.read<AuthProvider>().user?.role ?? UserRole.guest;

  Future<void> _pickFarmerMedia() async {
    final result = await FilePicker.platform.pickFiles(
      allowMultiple: false,
      type: FileType.custom,
      allowedExtensions: const ['jpg', 'jpeg', 'png', 'webp', 'mp4', 'mov', 'm4v', 'avi'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;
    setState(() {
      _selectedFile = result.files.first;
      _message = null;
    });
  }

  Future<void> _uploadFarmerMedia() async {
    final file = _selectedFile;
    final farmId = _farmIdController.text.trim();
    if (file == null) {
      setState(() => _message = 'Choose a crop photo or video first.');
      return;
    }
    if (farmId.isEmpty) {
      setState(() => _message = 'Enter the Farm public ID from FarmNex.');
      return;
    }

    setState(() {
      _uploading = true;
      _message = null;
    });
    try {
      final MultipartFile part;
      if (file.bytes != null) {
        part = MultipartFile.fromBytes(file.bytes!, filename: file.name);
      } else if (file.path != null) {
        part = await MultipartFile.fromFile(file.path!, filename: file.name);
      } else {
        throw StateError('The selected file cannot be read on this device.');
      }
      await _backend.uploadFarmFile(
        farmId,
        FormData.fromMap({'file': part}),
      );
      if (!mounted) return;
      setState(() {
        _message = 'Uploaded ${file.name} to the FarmNex farm file.';
        _selectedFile = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _message = 'Upload failed: ${e.toString()}');
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _pickDocuments() async {
    final result = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'jpg', 'jpeg', 'png', 'webp', 'doc', 'docx'],
      withData: true,
    );
    if (result == null) return;
    setState(() {
      _documents.addAll(result.files);
      _message = '${result.files.length} document(s) selected.';
    });
  }

  @override
  Widget build(BuildContext context) {
    final role = _role;
    return Scaffold(
      appBar: AppBar(title: AutoTranslatedText('Upload Center')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _header(role),
          const SizedBox(height: 14),
          if (role == UserRole.farmer) _farmerCard() else _documentCard(role),
          if (_message != null) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.primaryGreen.withValues(alpha: 0.07),
                borderRadius: BorderRadius.circular(14),
              ),
              child: AutoTranslatedText(_message!, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
            ),
          ],
        ],
      ),
    );
  }

  Widget _header(UserRole role) => Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [AppTheme.primaryGreen, AppTheme.accentTeal],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(22),
        ),
        child: Row(
          children: [
            AutoTranslatedText(role == UserRole.farmer ? '🌾' : '📄', style: const TextStyle(fontSize: 32)),
            const SizedBox(width: 14),
            Expanded(
              child: AutoTranslatedText(
                role == UserRole.farmer
                    ? 'Crop photos & videos'
                    : 'Documents & verification files',
                style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900),
              ),
            ),
          ],
        ),
      );

  Widget _farmerCard() => _card(
        title: '🌱 Farmer media',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AutoTranslatedText(
              'Choose crop photos or videos to add to this farm lot.',
              style: TextStyle(fontSize: 11.5, color: AppTheme.textMuted, height: 1.4),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _farmIdController,
              decoration: const InputDecoration(
                labelText: 'Farm public ID',
                prefixIcon: Icon(Icons.agriculture_outlined),
              ),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _uploading ? null : _pickFarmerMedia,
              icon: const Icon(Icons.photo_library_outlined),
              label: AutoTranslatedText(_selectedFile == null ? 'Choose photo / video' : _selectedFile!.name),
            ),
            const SizedBox(height: 10),
            ElevatedButton.icon(
              onPressed: _uploading ? null : _uploadFarmerMedia,
              icon: _uploading
                  ? const SizedBox(width: 17, height: 17, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.cloud_upload_outlined),
              label: AutoTranslatedText('Upload to FarmNex'),
            ),
          ],
        ),
      );

  Widget _documentCard(UserRole role) => _card(
        title: role == UserRole.buyer ? '🏢 Buyer documents' : '🚚 Logistics documents',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            AutoTranslatedText(
              'Choose documents for your account verification.',
              style: TextStyle(fontSize: 11.5, color: AppTheme.textMuted, height: 1.4),
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: _pickDocuments,
              icon: const Icon(Icons.attach_file),
              label: AutoTranslatedText('Select documents'),
            ),
            if (_documents.isNotEmpty) ...[
              const SizedBox(height: 12),
              ..._documents.map(
                (file) => ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.description_outlined),
                  title: AutoTranslatedText(file.name, maxLines: 1, overflow: TextOverflow.ellipsis),
                  subtitle: AutoTranslatedText('${((file.size) / 1024).toStringAsFixed(0)} KB'),
                  trailing: IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => setState(() => _documents.remove(file)),
                  ),
                ),
              ),
            ],
            const SizedBox(height: 8),
            AutoTranslatedText(
              '',
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppTheme.accentAmber),
            ),
          ],
        ),
      );

  Widget _card({required String title, required Widget child}) => Container(
        padding: const EdgeInsets.all(18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: AppTheme.borderLight),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AutoTranslatedText(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
            const SizedBox(height: 12),
            child,
          ],
        ),
      );
}
