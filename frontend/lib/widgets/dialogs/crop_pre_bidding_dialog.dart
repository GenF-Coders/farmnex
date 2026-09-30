import '../auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../models/bid_model.dart';
import '../../models/crop_model.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../providers/bidding_provider.dart';
import '../../localization/l10n_extension.dart';
import '../symbol_widgets.dart';

/// Pre-bidding room for one lot (`crop.id` is the listing's public id).
/// Buyer: place a bid. The lot's farmer: open the event, then accept a bid.
class CropPreBiddingDialog extends StatefulWidget {
  final CropItem crop;

  const CropPreBiddingDialog({super.key, required this.crop});

  @override
  State<CropPreBiddingDialog> createState() => _CropPreBiddingDialogState();
}

class _CropPreBiddingDialogState extends State<CropPreBiddingDialog> {
  final _bidController = TextEditingController();
  final _quantityController = TextEditingController();
  final _startController = TextEditingController();
  final _incrementController = TextEditingController(text: '10');
  final _hoursController = TextEditingController(text: '48');
  String? _message;
  bool _messageIsError = false;

  @override
  void initState() {
    super.initState();
    _startController.text = widget.crop.currentPrice.toStringAsFixed(0);
    _quantityController.text = widget.crop.quantityAvailable > 0 ? widget.crop.quantityAvailable.toString() : '1';
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final bidding = context.read<BiddingProvider>();
      await bidding.load();
      if (!mounted) return;
      _suggestNextBid(bidding);
    });
  }

  void _suggestNextBid(BiddingProvider bidding) {
    final event = bidding.openEventForListing(widget.crop.id);
    if (event == null) return;
    final next = (bidding.highestBid(event.publicId) ?? 0) + event.minimumIncrement;
    final first = next > event.startingPrice ? next : event.startingPrice;
    _bidController.text = first.toStringAsFixed(0);
  }

  @override
  void dispose() {
    _bidController.dispose();
    _quantityController.dispose();
    _startController.dispose();
    _incrementController.dispose();
    _hoursController.dispose();
    super.dispose();
  }

  void _show(String? error, String success) {
    if (!mounted) return;
    setState(() {
      _messageIsError = error != null;
      _message = error ?? success;
    });
  }

  Future<void> _submitBid(BidEventModel event) async {
    final amount = double.tryParse(_bidController.text.trim());
    final quantity = double.tryParse(_quantityController.text.trim());
    if (amount == null || amount <= 0 || quantity == null || quantity <= 0) {
      _show('Enter a bid price and a quantity.', '');
      return;
    }
    final bidding = context.read<BiddingProvider>();
    final error = await bidding.placeBid(eventId: event.publicId, amount: amount, quantity: quantity);
    if (error == null && mounted) _suggestNextBid(bidding);
    _show(error, 'Bid placed. The farmer can accept it any time.');
  }

  Future<void> _openEvent() async {
    final start = double.tryParse(_startController.text.trim());
    final increment = double.tryParse(_incrementController.text.trim());
    final hours = int.tryParse(_hoursController.text.trim());
    if (start == null || start <= 0 || increment == null || increment <= 0 || hours == null || hours <= 0) {
      _show('Enter a starting price, a minimum step and the hours bidding stays open.', '');
      return;
    }
    final error = await context.read<BiddingProvider>().openEvent(
          listingId: widget.crop.id,
          startingPrice: start,
          minimumIncrement: increment,
          duration: Duration(hours: hours),
        );
    _show(error, 'Bidding is open for buyers.');
  }

  Future<void> _accept(BidModel bid) async {
    String? orderNumber;
    final error = await context.read<BiddingProvider>().acceptBid(bid.publicId, onAccepted: (n) => orderNumber = n);
    _show(error, 'Bid accepted. ${orderNumber != null ? 'Order $orderNumber was' : 'An order was'} created for the buyer.');
  }

  Widget _banner() {
    if (_message == null || _message!.isEmpty) return const SizedBox.shrink();
    final color = _messageIsError ? AppTheme.alertRed : AppTheme.primaryGreen;
    return Container(
      padding: const EdgeInsets.all(12),
      margin: const EdgeInsets.only(bottom: 14),
      decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(12)),
      child: Row(
        children: [
          Icon(_messageIsError ? Icons.error_outline : Icons.check_circle, color: Colors.white, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: AutoTranslatedText(
              _message!,
              style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
            ),
          ),
        ],
      ),
    );
  }

  Widget _field(TextEditingController c, String label, {String? prefix}) => TextField(
        controller: c,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          prefixText: prefix,
          labelText: label,
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        ),
      );

  Widget _bidRow(BidModel bid, {required bool isHighest, required bool isMine, VoidCallback? onAccept}) {
    final who = isMine ? 'You' : 'Buyer ${bid.bidderId.substring(0, 6)}';
    final qty = bid.quantity == null
        ? ''
        : '${bid.quantity!.toStringAsFixed(bid.quantity! % 1 == 0 ? 0 : 2)} ${widget.crop.unit} • ';
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: isHighest ? const Color(0xFFF0FDF4) : Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: isHighest ? AppTheme.primaryGreen.withValues(alpha: 0.4) : AppTheme.borderLight),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 16,
            backgroundColor: isHighest ? AppTheme.primaryGreen : Colors.grey.shade200,
            child: Icon(isHighest ? Icons.emoji_events : Icons.person, size: 16, color: isHighest ? Colors.white : Colors.grey.shade700),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText(who, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700)),
                AutoTranslatedText(
                  '$qty${bidTimeAgo(bid.placedAt)} • ${bid.status}',
                  style: const TextStyle(fontSize: 10, color: AppTheme.textMuted),
                ),
              ],
            ),
          ),
          AutoTranslatedText(
            formatRupees(bid.amount),
            style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900, color: isHighest ? AppTheme.primaryGreen : AppTheme.textDark),
          ),
          if (onAccept != null) ...[
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed: onAccept,
              style: ElevatedButton.styleFrom(minimumSize: const Size(0, 34), padding: const EdgeInsets.symmetric(horizontal: 10)),
              child: const AutoTranslatedText('Accept', style: TextStyle(fontSize: 12)),
            ),
          ],
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    final role = user?.role ?? UserRole.guest;
    final bidding = context.watch<BiddingProvider>();
    final isOwner = role == UserRole.farmer && user?.id == widget.crop.farmerId;
    final event = bidding.openEventForListing(widget.crop.id);
    final bids = event == null ? <BidModel>[] : bidding.bidsForEvent(event.publicId);
    final highest = event == null ? null : bidding.highestBid(event.publicId);
    final busy = bidding.isBusy;

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
                  _banner(),
                  if (bidding.isLoading) const LinearProgressIndicator(),
                  if (bidding.error != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: AutoTranslatedText(bidding.error!, style: const TextStyle(fontSize: 12, color: AppTheme.alertRed)),
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
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        AutoTranslatedText(
                          event == null ? 'NO BIDDING OPEN' : (highest != null ? 'HIGHEST BID' : 'STARTING PRICE'),
                          style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: AppTheme.primaryGreen, letterSpacing: 0.5),
                        ),
                        const SizedBox(height: 4),
                        AutoTranslatedText(
                          formatRupees(event == null ? widget.crop.currentPrice : (highest ?? event.startingPrice)),
                          style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen),
                        ),
                        AutoTranslatedText(
                          event == null
                              ? 'per ${widget.crop.unit} • ${widget.crop.quantityAvailable} ${widget.crop.unit} available'
                              : 'per ${widget.crop.unit} • next bid at least +${formatRupees(event.minimumIncrement)} • closes ${event.endsAt.toLocal().toString().substring(0, 16)}',
                          style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (event == null)
                    AutoTranslatedText(
                      isOwner
                          ? 'Open bidding on this lot. Buyers then bid, and you accept the bid you like.'
                          : 'The farmer has not opened bidding on this lot yet.',
                      style: const TextStyle(fontSize: 12, color: AppTheme.textMuted),
                    )
                  else ...[
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        AutoTranslatedText(isOwner ? 'Bids on your lot' : 'Your bids', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
                        AutoTranslatedText('${bids.length} Offers', style: const TextStyle(fontSize: 11, color: AppTheme.textMuted)),
                      ],
                    ),
                    const SizedBox(height: 8),
                    if (bids.isEmpty)
                      const AutoTranslatedText('No bids yet.', style: TextStyle(fontSize: 12, color: AppTheme.textMuted)),
                    ...bids.map((bid) => _bidRow(
                          bid,
                          isHighest: bid.publicId == bids.first.publicId,
                          isMine: bid.bidderId == user?.id,
                          onAccept: isOwner && bid.isActive && !busy ? () => _accept(bid) : null,
                        )),
                  ],
                ],
              ),
            ),

            Container(
              padding: const EdgeInsets.all(16),
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.vertical(bottom: Radius.circular(24)),
                border: Border(top: BorderSide(color: AppTheme.borderLight)),
              ),
              child: _footer(role, isOwner, event, busy),
            ),
          ],
        ),
      ),
    );
  }

  Widget _footer(UserRole role, bool isOwner, BidEventModel? event, bool busy) {
    if (isOwner && event == null) {
      return Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              Expanded(child: _field(_startController, 'Starting price', prefix: '₹ ')),
              const SizedBox(width: 8),
              Expanded(child: _field(_incrementController, 'Min step', prefix: '₹ ')),
              const SizedBox(width: 8),
              Expanded(child: _field(_hoursController, 'Hours open')),
            ],
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: busy ? null : _openEvent,
              style: ElevatedButton.styleFrom(minimumSize: const Size(0, 48)),
              child: const AutoTranslatedText('Open bidding'),
            ),
          ),
        ],
      );
    }
    if (role == UserRole.buyer && event != null) {
      return Row(
        children: [
          Expanded(flex: 2, child: _field(_bidController, 'Price per ${widget.crop.unit}', prefix: '₹ ')),
          const SizedBox(width: 8),
          Expanded(flex: 2, child: _field(_quantityController, 'Quantity (${widget.crop.unit})')),
          const SizedBox(width: 8),
          Expanded(
            flex: 2,
            child: ElevatedButton(
              onPressed: busy ? null : () => _submitBid(event),
              style: ElevatedButton.styleFrom(minimumSize: const Size(0, 48)),
              child: AutoTranslatedText(context.t('place_bid')),
            ),
          ),
        ],
      );
    }
    return Row(
      children: [
        Expanded(
          child: AutoTranslatedText(
            role == UserRole.buyer
                ? 'You can bid once the farmer opens bidding.'
                : (role == UserRole.guest ? 'Log in as a buyer to place bids.' : 'Buyers place bids; farmers accept them.'),
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700),
          ),
        ),
        TextButton(onPressed: () => Navigator.of(context).pop(), child: const AutoTranslatedText('Done')),
      ],
    );
  }
}
