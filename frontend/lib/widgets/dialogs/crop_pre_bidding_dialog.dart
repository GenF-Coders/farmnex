import '../auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/guards/auth_guard.dart';
import '../../core/theme/app_theme.dart';
import '../../models/crop_model.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/bidding_provider.dart';
import '../../localization/l10n_extension.dart';

class CropPreBiddingDialog extends StatefulWidget {
  final CropItem crop;

  const CropPreBiddingDialog({super.key, required this.crop});

  @override
  State<CropPreBiddingDialog> createState() => _CropPreBiddingDialogState();
}

class _CropPreBiddingDialogState extends State<CropPreBiddingDialog> {
  late TextEditingController _bidController;
  bool _showSuccess = false;

  @override
  void initState() {
    super.initState();
    final bidding = context.read<BiddingProvider>();
    bidding.startListeningToBids(widget.crop.id);

    final highest = bidding.getHighestBid(widget.crop.id, widget.crop.currentPrice);
    _bidController = TextEditingController(text: (highest + 50).toStringAsFixed(0));
  }

  @override
  void dispose() {
    context.read<BiddingProvider>().stopListeningToBids();
    _bidController.dispose();
    super.dispose();
  }

  void _submitBid() {
    final auth = context.read<AuthProvider>();
    final bidding = context.read<BiddingProvider>();
    if (auth.user?.role == UserRole.farmer) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: AutoTranslatedText('Farmers sell crops; buyers place purchase bids.')),
      );
      return;
    }

    AuthGuard.requireAuth(
      context: context,
      authProvider: auth,
      actionType: 'bid',
      cropId: widget.crop.id,
      cropName: widget.crop.name,
      actionReason: 'Please login as a verified buyer to submit contract bids',
      onAuthenticated: () {
        final amount = double.tryParse(_bidController.text) ?? widget.crop.currentPrice + 50;
        bidding.placeBid(
          cropId: widget.crop.id,
          buyerName: auth.user?.name ?? 'Verified Buyer',
          companyName: auth.user?.companyName ?? 'Registered Mandi Firm',
          amount: amount,
        );

        if (mounted) {
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
    final auth = context.watch<AuthProvider>();
    final role = auth.user?.role ?? UserRole.guest;
    final isFarmer = role == UserRole.farmer;
    final bidding = context.watch<BiddingProvider>();
    final bids = bidding.getBidsForCrop(widget.crop.id);
    final highestBid = bidding.getHighestBid(widget.crop.id, widget.crop.currentPrice);

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
      backgroundColor: Colors.white,
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 20),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 540, maxHeight: 720),
        child: Column(
          children: [

            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              decoration: const BoxDecoration(
                color: Color(0xFFF9FAFB),
                borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
                border: Border(bottom: BorderSide(color: AppTheme.borderLight)),
              ),
              child: Row(
                children: [
                  AutoTranslatedText(widget.crop.emoji, style: const TextStyle(fontSize: 28)),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Flexible(
                              child: AutoTranslatedText(
                                widget.crop.name,
                                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(width: 6),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: AppTheme.primaryGreen.withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: AutoTranslatedText(
                                'Pre-Bidding Active',
                                style: TextStyle(
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                  color: AppTheme.primaryGreen,
                                ),
                              ),
                            ),
                          ],
                        ),
                        AutoTranslatedText(
                          '${widget.crop.variety} • ${widget.crop.farmerName} • ${widget.crop.location}',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: AppTheme.textMuted),
                    onPressed: () => Navigator.of(context).pop(),
                  ),
                ],
              ),
            ),

            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [

                  if (_showSuccess)
                    Container(
                      padding: const EdgeInsets.all(12),
                      margin: const EdgeInsets.only(bottom: 14),
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
                              'Bid broadcasted via WebSocket! You are now highest bidder.',
                              style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
                            ),
                          ),
                        ],
                      ),
                    ),

                  if (widget.crop.lastTwoDaysAIActive) ...[
                    Container(
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        gradient: LinearGradient(
                          colors: [
                            const Color(0xFFFEF3C7),
                            const Color(0xFFFFFBEB),
                          ],
                        ),
                        borderRadius: BorderRadius.circular(16),
                        border: Border.all(color: const Color(0xFFFDE68A)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              const Row(
                                children: [
                                  Icon(Icons.auto_awesome, color: Color(0xFFD97706), size: 18),
                                  SizedBox(width: 6),
                                  AutoTranslatedText(
                                    '48-Hour AI Maximum Price Predictor',
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w800,
                                      color: Color(0xFF92400E),
                                    ),
                                  ),
                                ],
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                                decoration: BoxDecoration(
                                  color: const Color(0xFFF59E0B),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: AutoTranslatedText(
                                  '${widget.crop.aiConfidence ?? 86}% Confidence',
                                  style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  AutoTranslatedText('Current Spot Price', style: TextStyle(fontSize: 11, color: Color(0xFFB45309))),
                                  AutoTranslatedText(
                                    '₹${widget.crop.currentPrice.toInt()}/${widget.crop.unit}',
                                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold, color: Color(0xFF78350F)),
                                  ),
                                ],
                              ),
                              const Icon(Icons.arrow_forward, color: Color(0xFFD97706), size: 18),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  AutoTranslatedText('Expected Max AI Target', style: TextStyle(fontSize: 11, color: Color(0xFFB45309))),
                                  AutoTranslatedText(
                                    '₹${widget.crop.expectedMaxPrice?.toInt() ?? 2550}/${widget.crop.unit}',
                                    style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900, color: Color(0xFF166534)),
                                  ),
                                ],
                              ),
                            ],
                          ),
                          if (widget.crop.aiReasons.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            const Divider(height: 1, color: Color(0xFFFDE68A)),
                            const SizedBox(height: 6),
                            ...widget.crop.aiReasons.map(
                              (reason) => Padding(
                                padding: const EdgeInsets.only(bottom: 3),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    AutoTranslatedText('• ', style: TextStyle(color: Color(0xFF92400E), fontSize: 11)),
                                    Expanded(
                                      child: AutoTranslatedText(
                                        reason,
                                        style: const TextStyle(fontSize: 11, color: Color(0xFF78350F)),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryGreen.withValues(alpha: 0.06),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: AppTheme.primaryGreen.withValues(alpha: 0.2)),
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Container(
                                  width: 8,
                                  height: 8,
                                  decoration: const BoxDecoration(
                                    color: Colors.green,
                                    shape: BoxShape.circle,
                                  ),
                                ),
                                const SizedBox(width: 6),
                                AutoTranslatedText(
                                  'LIVE HIGHEST BID',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w800,
                                    color: AppTheme.primaryGreen,
                                    letterSpacing: 0.5,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            AutoTranslatedText(
                              '₹${highestBid.toInt()}',
                              style: const TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.w900,
                                color: AppTheme.primaryGreen,
                              ),
                            ),
                            AutoTranslatedText(
                              'per ${widget.crop.unit} • ${widget.crop.quantityAvailable} units total',
                              style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                            ),
                          ],
                        ),
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.end,
                          children: [
                            AutoTranslatedText('Harvest Date', style: TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                            AutoTranslatedText(
                              widget.crop.expectedHarvestDate,
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textDark),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      AutoTranslatedText('Active Bidders (Live WebSocket Feed)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                      AutoTranslatedText('${bids.length} Offers', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                    ],
                  ),
                  const SizedBox(height: 8),

                  ...bids.map((bid) => Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: bid.isHighest ? const Color(0xFFF0FDF4) : Colors.white,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(
                            color: bid.isHighest ? AppTheme.primaryGreen.withValues(alpha: 0.4) : AppTheme.borderLight,
                          ),
                        ),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  radius: 16,
                                  backgroundColor: bid.isHighest ? AppTheme.primaryGreen : Colors.grey.shade200,
                                  child: Icon(
                                    bid.isHighest ? Icons.emoji_events : Icons.person,
                                    size: 16,
                                    color: bid.isHighest ? Colors.white : Colors.grey.shade700,
                                  ),
                                ),
                                const SizedBox(width: 10),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        AutoTranslatedText(
                                          bid.companyName,
                                          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                                        ),
                                        if (bid.verifiedBuyer) ...[
                                          const SizedBox(width: 4),
                                          const Icon(Icons.verified, color: Colors.blue, size: 14),
                                        ],
                                      ],
                                    ),
                                    AutoTranslatedText(
                                      '${bid.buyerName} • ${bid.timestamp}',
                                      style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                            AutoTranslatedText(
                              '₹${bid.amount.toInt()}',
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: FontWeight.w900,
                                color: bid.isHighest ? AppTheme.primaryGreen : AppTheme.textDark,
                              ),
                            ),
                          ],
                        ),
                      )),
                ],
              ),
            ),

            if (isFarmer)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.vertical(bottom: Radius.circular(24)),
                  border: Border(top: BorderSide(color: AppTheme.borderLight)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.sell_outlined, color: AppTheme.primaryGreen),
                    const SizedBox(width: 10),
                    Expanded(
                      child: AutoTranslatedText(
                        'Selling price: ₹${widget.crop.currentPrice.toInt()}/${widget.crop.unit}',
                        style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w800),
                      ),
                    ),
                    TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: AutoTranslatedText('Done'),
                    ),
                  ],
                ),
              )
            else
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.vertical(bottom: Radius.circular(24)),
                  border: Border(top: BorderSide(color: AppTheme.borderLight)),
                ),
                child: Row(
                  children: [
                    Expanded(
                      flex: 2,
                      child: TextField(
                        controller: _bidController,
                        keyboardType: TextInputType.number,
                        decoration: InputDecoration(
                          prefixText: '₹ ',
                          labelText: 'Your Bid Offer',
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: _submitBid,
                        style: ElevatedButton.styleFrom(minimumSize: const Size(0, 48)),
                        child: AutoTranslatedText(context.t('place_bid')),
                      ),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }
}
