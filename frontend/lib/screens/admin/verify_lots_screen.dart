import 'package:flutter/material.dart';

import '../../core/network/listing_api.dart' show listingErrorMessage;
import '../../core/network/listing_media_api.dart';
import '../../core/theme/app_theme.dart';
import '../../models/listing_media_model.dart';
import '../../widgets/auto_translated_text.dart';
import '../../widgets/listing_media_section.dart';

/// Admin: lots whose farmer added photos/videos and that wait for a FarmNex check.
class AdminVerifyLotsScreen extends StatefulWidget {
  const AdminVerifyLotsScreen({super.key});

  @override
  State<AdminVerifyLotsScreen> createState() => _AdminVerifyLotsScreenState();
}

class _AdminVerifyLotsScreenState extends State<AdminVerifyLotsScreen> {
  final _api = ListingMediaApi();
  List<VerificationQueueItem>? _queue;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _error = null);
    try {
      final queue = await _api.queue();
      if (mounted) setState(() => _queue = queue);
    } catch (e) {
      if (mounted) setState(() => _error = listingErrorMessage(e));
    }
  }

  Future<void> _decide(VerificationQueueItem lot, {required bool verify}) async {
    final messenger = ScaffoldMessenger.of(context);
    String? reason;
    if (!verify) {
      reason = await _askReason();
      if (reason == null) return; // cancelled
    }
    try {
      await _api.decide(lot.listingId, decision: verify ? 'VERIFIED' : 'REJECTED', reason: reason);
      messenger.showSnackBar(SnackBar(
        content: AutoTranslatedText(verify ? '✅ ${lot.title} verified.' : '❌ ${lot.title} rejected. The farmer sees why.'),
        backgroundColor: verify ? AppTheme.primaryGreen : null,
      ));
      await _load();
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: AutoTranslatedText('⚠️ ${listingErrorMessage(e)}')));
    }
  }

  Future<String?> _askReason() {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const AutoTranslatedText('Why is it not verified?'),
        content: TextField(
          controller: controller,
          maxLength: 500,
          decoration: const InputDecoration(hintText: 'e.g. Photo is blurry, crop not visible'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext), child: const AutoTranslatedText('Cancel')),
          TextButton(
            onPressed: () {
              final text = controller.text.trim();
              if (text.isNotEmpty) Navigator.pop(dialogContext, text);
            },
            child: const AutoTranslatedText('Reject'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final queue = _queue;
    Widget body;
    if (_error != null) {
      body = Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          AutoTranslatedText('⚠️ $_error'),
          TextButton(onPressed: _load, child: const AutoTranslatedText('Try again')),
        ]),
      );
    } else if (queue == null) {
      body = const Center(child: CircularProgressIndicator());
    } else if (queue.isEmpty) {
      body = ListView(children: const [
        SizedBox(height: 120),
        Center(child: AutoTranslatedText('🎉 No lots waiting for a check.')),
      ]);
    } else {
      body = ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: queue.length,
        itemBuilder: (_, i) {
          final lot = queue[i];
          return Card(
            key: ValueKey(lot.listingId),
            elevation: 0,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(16),
              side: const BorderSide(color: AppTheme.borderLight),
            ),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                AutoTranslatedText(lot.title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
                AutoTranslatedText(
                  '${lot.listingType == 'PRE_BID' ? '⚖️ Pre-bid' : '🛒 Fixed price'} • ₹${lot.price.round()}/${lot.unit} • ${lot.mediaCount} file(s)',
                  style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                ),
                ListingMediaSection(listingId: lot.listingId),
                const SizedBox(height: 8),
                Row(children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => _decide(lot, verify: false),
                      child: const AutoTranslatedText('❌ Reject'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () => _decide(lot, verify: true),
                      style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryGreen),
                      child: const AutoTranslatedText('✅ Verify'),
                    ),
                  ),
                ]),
              ]),
            ),
          );
        },
      );
    }
    return Scaffold(
      appBar: AppBar(title: const AutoTranslatedText('🔍 Verify lots')),
      body: RefreshIndicator(onRefresh: _load, child: body),
    );
  }
}
