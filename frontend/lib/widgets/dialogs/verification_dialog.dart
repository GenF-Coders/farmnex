import '../auto_translated_text.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_theme.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/verification_provider.dart';

class VerificationDialog extends StatefulWidget {
  const VerificationDialog({super.key});

  @override
  State<VerificationDialog> createState() => _VerificationDialogState();
}

class _VerificationDialogState extends State<VerificationDialog> {
  final _docNumberController = TextEditingController();
  String _docType = '';
  PlatformFile? _file;
  String? _successMessage;

  @override
  void initState() {
    super.initState();
    final role = context.read<AuthProvider>().user?.role ?? UserRole.farmer;
    _docType = _defaultDocType(role);
  }

  @override
  void dispose() {
    _docNumberController.dispose();
    super.dispose();
  }

  String _defaultDocType(UserRole role) {
    switch (role) {
      case UserRole.farmer:
        return '7/12 Land Record';
      case UserRole.buyer:
        return 'GSTIN / APMC License';
      case UserRole.logistics:
        return 'Vehicle RC / Permit';
      case UserRole.admin:
        return 'Identity Document';
      case UserRole.guest:
        return 'Identity Document';
    }
  }

  String _roleKey(UserRole role) {
    switch (role) {
      case UserRole.logistics:
        return 'logistics';
      case UserRole.farmer:
        return 'farmer';
      case UserRole.buyer:
        return 'buyer';
      case UserRole.admin:
        return 'admin';
      case UserRole.guest:
        return 'guest';
    }
  }

  List<String> _docTypes(UserRole role) {
    switch (role) {
      case UserRole.farmer:
        return const ['7/12 Land Record', 'Aadhaar Card'];
      case UserRole.buyer:
        return const ['GSTIN / APMC License', 'Aadhaar Card'];
      case UserRole.logistics:
        return const ['Vehicle RC / Permit', 'Aadhaar Card'];
      case UserRole.admin:
        return const ['Identity Document', 'Aadhaar Card'];
      case UserRole.guest:
        return const ['Identity Document'];
    }
  }

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['pdf', 'jpg', 'jpeg', 'png', 'webp'],
      withData: true,
    );
    if (result != null && result.files.isNotEmpty && mounted) {
      setState(() => _file = result.files.first);
    }
  }

  void _submit(UserModel user) {
    if (_file == null) {
      setState(() => _successMessage = 'Select a document file first.');
      return;
    }
    if (_docNumberController.text.trim().isEmpty) {
      setState(() => _successMessage = 'Enter the document number.');
      return;
    }

    final ver = context.read<VerificationProvider>();
    ver.submitDocument(
      userType: _roleKey(user.role),
      fullName: user.name,
      phone: user.mobile,
      docType: _docType,
      docNumber: _docNumberController.text.trim(),
      filePath: _file?.path,
    );
    setState(() => _successMessage = 'Document submitted.');
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthProvider>().user;
    final ver = context.watch<VerificationProvider>();
    if (user == null || user.role == UserRole.guest) {
      return const AlertDialog(content: AutoTranslatedText('Please sign in to open KYC.'));
    }
    final docs = ver.documents.where((d) => d.userType == _roleKey(user.role)).toList();
    final types = _docTypes(user.role);

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
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
                  const Icon(Icons.verified_user, color: Colors.white),
                  const SizedBox(width: 12),
                  Expanded(
                    child: AutoTranslatedText('${user.role.displayName} KYC', style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.w800)),
                  ),
                  IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close, color: Colors.white)),
                ],
              ),
            ),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  AutoTranslatedText('Upload documents for ${user.name}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: _docType,
                    decoration: const InputDecoration(labelText: 'Document type', prefixIcon: Icon(Icons.badge_outlined)),
                    items: types.map((t) => DropdownMenuItem(value: t, child: AutoTranslatedText(t))).toList(),
                    onChanged: (v) => setState(() => _docType = v ?? _docType),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _docNumberController,
                    decoration: InputDecoration(
                      labelText: _docType == 'Aadhaar Card' ? 'Aadhaar number' : 'Document number',
                      prefixIcon: const Icon(Icons.numbers_outlined),
                    ),
                  ),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                    onPressed: _pickFile,
                    icon: const Icon(Icons.upload_file),
                    label: AutoTranslatedText(_file == null ? 'Choose PDF or image' : _file!.name, overflow: TextOverflow.ellipsis),
                  ),
                  if (_successMessage != null) ...[
                    const SizedBox(height: 10),
                    AutoTranslatedText(_successMessage!, textAlign: TextAlign.center, style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: AppTheme.primaryGreen)),
                  ],
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    onPressed: ver.isUploading ? null : () => _submit(user),
                    icon: ver.isUploading ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : const Icon(Icons.check),
                    label: AutoTranslatedText('Submit KYC document'),
                  ),
                  const SizedBox(height: 24),
                  AutoTranslatedText('Submitted documents', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w800)),
                  const SizedBox(height: 8),
                  if (docs.isEmpty)
                    AutoTranslatedText('No documents uploaded yet.', style: TextStyle(fontSize: 11, color: AppTheme.textMuted))
                  else
                    ...docs.map((d) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: const Icon(Icons.description_outlined, color: AppTheme.primaryGreen),
                          title: AutoTranslatedText(d.docType, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
                          subtitle: AutoTranslatedText('${d.docNumber} • ${d.status}', style: const TextStyle(fontSize: 10.5)),
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
