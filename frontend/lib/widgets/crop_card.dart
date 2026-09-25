import 'auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/guards/auth_guard.dart';
import '../core/theme/app_theme.dart';
import '../models/crop_model.dart';
import '../models/user_model.dart';
import '../providers/auth_provider.dart';
import '../providers/cart_provider.dart';
import '../screens/payment/checkout_screen.dart';
import 'dialogs/ai_forecast_dialog.dart';
import 'dialogs/crop_pre_bidding_dialog.dart';
import 'crop_picture.dart';

class CropCard extends StatelessWidget {
  final CropItem crop;
  final VoidCallback? onInspect;

  const CropCard({super.key, required this.crop, this.onInspect});

  void _handleBuy(BuildContext context) {
    final auth = context.read<AuthProvider>();
    AuthGuard.requireAuth(
      context: context,
      authProvider: auth,
      actionType: 'buy',
      cropId: crop.id,
      cropName: crop.name,
      actionReason: 'Sign in as a buyer to purchase directly from the farmer.',
      onAuthenticated: () {
        final quantity = crop.quantityAvailable >= 10 ? 10 : crop.quantityAvailable;
        Navigator.of(context).push<bool>(
          MaterialPageRoute(
            builder: (_) => CheckoutScreen(
              title: 'Buy now',
              items: [
                CheckoutItem(
                  cropId: crop.id,
                  name: crop.name,
                  emoji: crop.emoji,
                  quantity: quantity <= 0 ? 1 : quantity,
                  unit: crop.unit,
                  pricePerUnit: crop.currentPrice,
                  farmerName: crop.farmerName,
                  location: crop.location,
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _handleAddToCart(BuildContext context) {
    final auth = context.read<AuthProvider>();
    AuthGuard.requireAuth(
      context: context,
      authProvider: auth,
      actionType: 'buy',
      cropId: crop.id,
      cropName: crop.name,
      actionReason: 'Sign in as a buyer to add produce to your cart.',
      onAuthenticated: () {
        context.read<CartProvider>().add(crop);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: AutoTranslatedText('${crop.name} added to cart.'),
            backgroundColor: AppTheme.primaryGreen,
          ),
        );
      },
    );
  }

  void _openBidding(BuildContext context) {
    showDialog(context: context, builder: (_) => CropPreBiddingDialog(crop: crop));
  }

  void _openForecast(BuildContext context) {
    showDialog(context: context, builder: (_) => AIForecastDialog(crop: crop));
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final role = auth.isLoggedIn ? (auth.user?.role ?? UserRole.guest) : UserRole.guest;
    final canBuy = role == UserRole.buyer || role == UserRole.guest;
    final isFarmer = role == UserRole.farmer;
    final inCart = context.watch<CartProvider>().contains(crop.id);

    return Card(
      clipBehavior: Clip.antiAlias,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(14),
        side: const BorderSide(color: AppTheme.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AspectRatio(
            aspectRatio: 1.22,
            child: Stack(
              fit: StackFit.expand,
              children: [
                Container(
                  color: const Color(0xFFF7F8F5),
                  padding: const EdgeInsets.all(10),
                  child: CropPicture(
                    cropName: crop.name,
                    fallbackEmoji: crop.emoji,
                    size: 200,
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
                if (crop.biddingActive)
                  Positioned(
                    left: 8,
                    top: 8,
                    child: _tag('Pre-bid', const Color(0xFFE7F6EA), AppTheme.primaryGreen),
                  ),
                if (crop.isPerishable)
                  Positioned(
                    right: 8,
                    top: 8,
                    child: _tag('Fresh', const Color(0xFFFFF3E6), const Color(0xFFB45309)),
                  ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(10, 10, 10, 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(
                  crop.name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w800, color: AppTheme.textDark),
                ),
                const SizedBox(height: 3),
                AutoTranslatedText(
                  crop.variety,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                ),
                const SizedBox(height: 7),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Expanded(
                      child: AutoTranslatedText(
                        '₹${crop.currentPrice.toInt()} / ${crop.unit}',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 14.5, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
                      ),
                    ),
                    Row(
                      children: [
                        Icon(crop.priceTrend >= 0 ? Icons.trending_up : Icons.trending_down, size: 13, color: crop.priceTrend >= 0 ? AppTheme.primaryGreen : AppTheme.alertRed),
                        AutoTranslatedText('${crop.priceTrend.abs().toStringAsFixed(1)}%', style: TextStyle(fontSize: 9.5, fontWeight: FontWeight.w800, color: crop.priceTrend >= 0 ? AppTheme.primaryGreen : AppTheme.alertRed)),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                AutoTranslatedText(
                  '${crop.quantityAvailable} ${crop.unit}s • ${crop.location}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 9.5, color: AppTheme.textMuted),
                ),
                const SizedBox(height: 9),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton(
                        onPressed: onInspect ?? () => _openBidding(context),
                        style: OutlinedButton.styleFrom(
                          minimumSize: const Size(0, 36),
                          padding: const EdgeInsets.symmetric(horizontal: 6),
                          side: const BorderSide(color: AppTheme.primaryGreen),
                          foregroundColor: AppTheme.primaryGreen,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
                        ),
                        child: AutoTranslatedText(crop.biddingActive ? 'View bids' : 'View', style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w800)),
                      ),
                    ),
                    if (canBuy) ...[
                      const SizedBox(width: 6),
                      SizedBox(
                        width: 40,
                        height: 36,
                        child: OutlinedButton(
                          onPressed: () => _handleAddToCart(context),
                          style: OutlinedButton.styleFrom(
                            padding: EdgeInsets.zero,
                            side: const BorderSide(color: AppTheme.borderLight),
                            foregroundColor: AppTheme.primaryGreen,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
                          ),
                          child: Icon(inCart ? Icons.check : Icons.shopping_cart_outlined, size: 17),
                        ),
                      ),
                      const SizedBox(width: 6),
                      SizedBox(
                        width: 42,
                        height: 36,
                        child: ElevatedButton(
                          onPressed: () => _handleBuy(context),
                          style: ElevatedButton.styleFrom(
                            padding: EdgeInsets.zero,
                            minimumSize: const Size(0, 36),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9)),
                          ),
                          child: const Icon(Icons.bolt_rounded, size: 18),
                        ),
                      ),
                    ],
                    if (isFarmer) ...[
                      const SizedBox(width: 6),
                      SizedBox(
                        width: 40,
                        height: 36,
                        child: OutlinedButton(
                          onPressed: () => _openForecast(context),
                          style: OutlinedButton.styleFrom(padding: EdgeInsets.zero, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(9))),
                          child: const Icon(Icons.auto_awesome, size: 16),
                        ),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _tag(String label, Color bg, Color fg) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 4),
        decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(7)),
        child: AutoTranslatedText(label, style: TextStyle(fontSize: 9, fontWeight: FontWeight.w800, color: fg)),
      );
}
