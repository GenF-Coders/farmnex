import 'package:flutter/material.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/dialogs/auth_dialog.dart';

class AuthGuard {

  static Future<void> requireAuth({
    required BuildContext context,
    required AuthProvider authProvider,
    required VoidCallback onAuthenticated,
    required String actionType,
    String? cropId,
    String? cropName,
    String actionReason = 'Please sign in or register to continue with this action',
  }) async {

    if (authProvider.isLoggedIn) {
      onAuthenticated();
      return;
    }

    authProvider.setPendingAction(
      PendingAction(type: actionType, cropId: cropId, cropName: cropName),
    );

    final success = await showDialog<bool>(
      context: context,
      barrierDismissible: true,
      builder: (ctx) => AuthDialog(
        reason: actionReason,
        initialRole: actionType == 'buy' ? UserRole.buyer : UserRole.farmer,
      ),
    );

    if (success == true && context.mounted) {
      onAuthenticated();
      authProvider.clearPendingAction();
    }
  }
}
