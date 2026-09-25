class VerificationDocument {
  final String id;
  final String userType;
  final String fullName;
  final String phone;
  final String docType;
  final String docNumber;
  final String? docUrl;
  final String status;
  final String submittedDate;
  final String? notes;

  const VerificationDocument({
    required this.id,
    required this.userType,
    required this.fullName,
    required this.phone,
    required this.docType,
    required this.docNumber,
    this.docUrl,
    required this.status,
    required this.submittedDate,
    this.notes,
  });

  VerificationDocument copyWith({
    String? status,
    String? notes,
  }) {
    return VerificationDocument(
      id: id,
      userType: userType,
      fullName: fullName,
      phone: phone,
      docType: docType,
      docNumber: docNumber,
      docUrl: docUrl,
      status: status ?? this.status,
      submittedDate: submittedDate,
      notes: notes ?? this.notes,
    );
  }
}
