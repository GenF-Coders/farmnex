import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';

/// CEDA's data terms require their logo and a text credit on every screen that shows these prices
/// (bottom right). Pass the `attribution` text the forecast API sends. The logo file is
/// `assets/branding/ceda_logo.png`; until it is added the text credit still shows.
class CedaCredit extends StatelessWidget {
  final String text;

  const CedaCredit({super.key, required this.text});

  @override
  Widget build(BuildContext context) {
    final credit = text.isEmpty ? 'Price data: CEDA, Ashoka University (Agmarknet)' : text;
    return Padding(
      padding: const EdgeInsets.only(top: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.end,
        children: [
          Flexible(
            child: Text(
              credit,
              textAlign: TextAlign.right,
              style: const TextStyle(fontSize: 9.5, color: AppTheme.textMuted),
            ),
          ),
          const SizedBox(width: 8),
          Image.asset(
            'assets/branding/ceda_logo.png',
            height: 28,
            errorBuilder: (context, error, stackTrace) => const SizedBox.shrink(),
          ),
        ],
      ),
    );
  }
}
