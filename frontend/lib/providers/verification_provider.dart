import 'package:flutter/material.dart';
import '../models/verification_model.dart';

class VerificationProvider extends ChangeNotifier {
  final List<VerificationDocument> _documents = [];
  bool _isUploading = false;
  String _selectedRole = 'farmer';

  List<VerificationDocument> get documents => _documents;
  bool get isUploading => _isUploading;
  String get selectedRole => _selectedRole;

  VerificationProvider() {
    _initDefaultDocuments();
  }

  void _initDefaultDocuments() {
    _documents.addAll([
      const VerificationDocument(
        id: 'doc-1',
        userType: 'farmer',
        fullName: 'Ramesh Patil',
        phone: '9823456789',
        docType: '7/12 Land Record (Satbara Utara)',
        docNumber: 'SURVEY-142/3 (4.5 Acres)',
        status: 'verified',
        submittedDate: 'Yesterday, 10:15 AM',
        notes: 'Document verified.',
      ),
      const VerificationDocument(
        id: 'doc-2',
        userType: 'buyer',
        fullName: 'Vikram Sethi (AgroCorp Ltd)',
        phone: '9811002233',
        docType: 'GSTIN & APMC Mandi License',
        docNumber: '27AABCA1234F1Z9',
        status: 'verified',
        submittedDate: '2 Days ago',
        notes: 'Business document verified.',
      ),
      const VerificationDocument(
        id: 'doc-3',
        userType: 'logistics',
        fullName: 'Gurpreet Singh',
        phone: '9877112244',
        docType: 'Commercial Heavy Vehicle RC',
        docNumber: 'MP-09-GH-4412 (16-Wheeler)',
        status: 'pending',
        submittedDate: '3 Days ago',
        notes: 'Document review in progress.',
      ),
    ]);
  }

  void setSelectedRole(String role) {
    _selectedRole = role;
    notifyListeners();
  }

  List<VerificationDocument> get filteredDocuments {
    return _documents.where((d) => d.userType == _selectedRole).toList();
  }

  Future<bool> submitDocument({
    required String userType,
    required String fullName,
    required String phone,
    required String docType,
    required String docNumber,
    String? filePath,
  }) async {
    _isUploading = true;
    notifyListeners();

    try {

      await Future.delayed(const Duration(milliseconds: 700));

      final newDoc = VerificationDocument(
        id: 'doc-${DateTime.now().millisecondsSinceEpoch}',
        userType: userType,
        fullName: fullName,
        phone: phone,
        docType: docType,
        docNumber: docNumber,
        status: 'pending',
        submittedDate: 'Just now',
        notes: 'Document submitted for verification.',
      );

      _documents.insert(0, newDoc);
      _isUploading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isUploading = false;
      notifyListeners();
      return false;
    }
  }

  void updateDocumentStatus(String docId, String status) {
    final index = _documents.indexWhere((d) => d.id == docId);
    if (index != -1) {
      _documents[index] = _documents[index].copyWith(status: status);
      notifyListeners();
    }
  }
}
