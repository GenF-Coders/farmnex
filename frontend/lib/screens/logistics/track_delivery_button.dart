import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

import '../../core/network/route_api.dart';
import '../../core/theme/app_theme.dart';
import '../../widgets/auto_translated_text.dart';

/// "Track" button for an order card. Give it the order's public id: it asks the backend for the
/// delivery status and ETA, then lets the buyer / farmer open the live map in a WebView.
class TrackDeliveryButton extends StatefulWidget {
  final String orderPublicId;
  const TrackDeliveryButton({super.key, required this.orderPublicId});

  @override
  State<TrackDeliveryButton> createState() => _TrackDeliveryButtonState();
}

class _TrackDeliveryButtonState extends State<TrackDeliveryButton> {
  bool _loading = false;

  Future<void> _open() async {
    setState(() => _loading = true);
    OrderDelivery? delivery;
    String? error;
    try {
      delivery = await RouteApi().orderDelivery(widget.orderPublicId);
    } catch (e) {
      error = routeErrorMessage(e);
    }
    if (!mounted) return;
    setState(() => _loading = false);

    if (error != null) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: AutoTranslatedText(error)));
      return;
    }
    if (delivery == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: AutoTranslatedText('🚚 No truck booked for this order yet.')),
      );
      return;
    }
    final found = delivery;
    await showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (_) => _DeliverySheet(delivery: found),
    );
  }

  @override
  Widget build(BuildContext context) {
    return OutlinedButton(
      onPressed: _loading ? null : _open,
      child: _loading
          ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
          : const AutoTranslatedText('🚚  Track'),
    );
  }
}

String _statusText(String status) {
  switch (status) {
    case 'pending':
      return '🕐 Waiting for a truck';
    case 'assigned':
      return '🚚 Truck assigned';
    case 'picked_up':
      return '📦 Picked up, on the way';
    case 'delivered':
      return '✅ Delivered';
    case 'cancelled':
      return '❌ Cancelled';
    default:
      return status;
  }
}

class _DeliverySheet extends StatelessWidget {
  final OrderDelivery delivery;
  const _DeliverySheet({required this.delivery});

  @override
  Widget build(BuildContext context) {
    final eta = delivery.etaMin;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 4, 20, 24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AutoTranslatedText(_statusText(delivery.status),
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w900)),
          const SizedBox(height: 8),
          if (delivery.vehicleNumber != null)
            AutoTranslatedText('🚛 ${delivery.vehicleNumber}', style: const TextStyle(fontSize: 12.5)),
          if (eta != null && !delivery.isDelivered)
            AutoTranslatedText('🕐 Arrives in about ${eta.round()} min', style: const TextStyle(fontSize: 12.5)),
          if (delivery.estimatedFare != null)
            AutoTranslatedText('🧾 Delivery fare ₹${delivery.estimatedFare!.round()}',
                style: const TextStyle(fontSize: 12.5, color: AppTheme.textMuted)),
          const SizedBox(height: 16),
          if (delivery.canTrack)
            SizedBox(
              width: double.infinity,
              height: 44,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  Navigator.of(context).push(
                    MaterialPageRoute<void>(builder: (_) => TrackMapScreen(url: delivery.trackingUrl!)),
                  );
                },
                child: const AutoTranslatedText('🗺️  Watch live on map'),
              ),
            ),
        ],
      ),
    );
  }
}

/// The live map page from the route optimizer, shown inside the app.
class TrackMapScreen extends StatefulWidget {
  final String url;
  const TrackMapScreen({super.key, required this.url});

  @override
  State<TrackMapScreen> createState() => _TrackMapScreenState();
}

class _TrackMapScreenState extends State<TrackMapScreen> {
  WebViewController? _controller;

  @override
  void initState() {
    super.initState();
    // Only open https links (Android blocks plain http in WebViews anyway).
    final uri = Uri.tryParse(widget.url);
    if (uri != null && uri.scheme == 'https') {
      _controller = WebViewController()
        ..setJavaScriptMode(JavaScriptMode.unrestricted)
        ..loadRequest(uri);
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;
    return Scaffold(
      appBar: AppBar(title: const AutoTranslatedText('🚚 Live tracking')),
      body: controller == null
          ? const Center(child: AutoTranslatedText('This tracking link cannot be opened.'))
          : WebViewWidget(controller: controller),
    );
  }
}
