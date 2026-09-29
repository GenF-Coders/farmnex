import '../../widgets/auto_translated_text.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../core/theme/app_theme.dart';
import '../../models/buyer_model.dart';
import '../../models/deal_model.dart';
import '../../models/user_model.dart';
import '../../providers/auth_provider.dart';
import '../../widgets/dialogs/auth_dialog.dart';
import '../../widgets/dialogs/language_selector_dialog.dart';
import '../../core/navigation/role_tabs.dart';
import '../../localization/l10n_extension.dart';
import '../../providers/logistics_provider.dart';
import '../../providers/payment_provider.dart';
import '../../widgets/dialogs/verification_dialog.dart';
import '../../widgets/symbol_widgets.dart';
import '../buyer/buyer_bids_screen.dart';
import '../payment/wallet_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  String _activeTab = 'deals';

  final List<CropDeal> _deals = [
    const CropDeal(
      id: 'deal-1',
      cropId: 'crop-1',
      cropName: 'Sharbati Wheat (गेहूं)',
      cropEmoji: '🌾',
      buyerName: 'Manoj Agarwal',
      buyerCompany: 'Kishanlal Agro Export Ltd',
      buyerLocation: 'Indore Mandi Yard',
      bidPrice: 2520,
      quantity: 100,
      unit: 'Quintals',
      totalAmount: 252000,
      harvestDate: '2 Days Left',
      status: 'pending',
      timestamp: '15 mins ago',
    ),
    const CropDeal(
      id: 'deal-2',
      cropId: 'crop-2',
      cropName: 'Yellow Soybean (सोयाबीन)',
      cropEmoji: '🌱',
      buyerName: 'Prakash Deshmukh',
      buyerCompany: 'Adani Wilmar Edible Oils',
      buyerLocation: 'Latur APMC',
      bidPrice: 4920,
      quantity: 50,
      unit: 'Quintals',
      totalAmount: 246000,
      harvestDate: '6 Days Left',
      status: 'accepted',
      timestamp: '2 hours ago',
    ),
  ];

  final List<BuyerBidItem> _buyerBids = [
    const BuyerBidItem(
      id: 'bb-1',
      cropId: 'crop-1',
      cropName: 'Sharbati Wheat - 100q',
      cropImage: '🌾',
      farmerName: 'Ramesh Patil (Indore)',
      mandiLocation: 'Indore APMC',
      myBidPrice: 2520,
      highestBidPrice: 2520,
      quantity: 100,
      unit: 'Quintal',
      status: 'winning',
      harvestDate: '2 Days Left',
      timestamp: 'Just now',
    ),
    const BuyerBidItem(
      id: 'bb-2',
      cropId: 'crop-2',
      cropName: 'Yellow Soybean - 50q',
      cropImage: '🌱',
      farmerName: 'Balasaheb Shinde (Latur)',
      mandiLocation: 'Latur Mandi',
      myBidPrice: 4880,
      highestBidPrice: 4920,
      quantity: 50,
      unit: 'Quintal',
      status: 'outbid',
      harvestDate: '6 Days Left',
      timestamp: '25 mins ago',
    ),
  ];

  void _acceptDeal(int index) {
    setState(() {
      _deals[index] = _deals[index].copyWith(status: 'accepted');
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: AutoTranslatedText('Deal accepted! ₹${_deals[index].totalAmount.toInt()} locked in escrow.'),
        backgroundColor: AppTheme.primaryGreen,
      ),
    );
  }

  void _declineDeal(int index) {
    setState(() {
      _deals[index] = _deals[index].copyWith(status: 'declined');
    });
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: AutoTranslatedText('Offer declined. Buyer notified.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    final role = auth.isLoggedIn ? (user?.role ?? UserRole.guest) : UserRole.guest;
    final isBuyer = role == UserRole.buyer;
    final isFarmer = role == UserRole.farmer;
    final isLogistics = role == UserRole.logistics;
    final isAdmin = role == UserRole.admin;

    final activeTab = isBuyer
        ? (_activeTab.startsWith('buyer_') || _activeTab == 'kyc' ? _activeTab : 'buyer_bids')
        : isFarmer
            ? (_activeTab.startsWith('buyer_') ? 'deals' : _activeTab)
            : 'kyc';

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [

        Container(
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(22),
            border: Border.all(color: AppTheme.borderLight),
          ),
          child: Row(
            children: [
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: AppTheme.primaryGreen.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(16),
                ),
                alignment: Alignment.center,
                child: AutoTranslatedText(
                  RoleTabs.symbolFor(role),
                  style: const TextStyle(fontSize: 26),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Flexible(
                          child: AutoTranslatedText(
                            auth.isLoggedIn ? (user?.name ?? 'Farmer User') : 'Guest User (अतिथि)',
                            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                        const SizedBox(width: 6),
                        if (auth.isLoggedIn && user?.isVerified == true)
                          const Icon(Icons.verified, color: Colors.blue, size: 16),
                      ],
                    ),
                    const SizedBox(height: 2),
                    AutoTranslatedText(
                      auth.isLoggedIn
                          ? '${user?.role.displayName} • ${user?.mobile}'
                          : 'No login active • Full browse access',
                      style: const TextStyle(fontSize: 11.5, color: AppTheme.textMuted),
                    ),
                    if (auth.isLoggedIn && user?.address.isNotEmpty == true)
                      AutoTranslatedText(
                        user!.address,
                        style: const TextStyle(fontSize: 11, color: AppTheme.textMuted),
                      ),
                  ],
                ),
              ),
              ElevatedButton(
                onPressed: () {
                  if (auth.isLoggedIn) {
                    auth.logout();
                  } else {
                    showDialog(context: context, builder: (_) => const AuthDialog());
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: auth.isLoggedIn ? const Color(0xFFF3F4F6) : AppTheme.primaryGreen,
                  foregroundColor: auth.isLoggedIn ? AppTheme.textDark : Colors.white,
                  minimumSize: const Size(0, 36),
                  padding: const EdgeInsets.symmetric(horizontal: 12),
                ),
                child: AutoTranslatedText(auth.isLoggedIn ? '🚪 Logout' : '🔐 Sign in', style: const TextStyle(fontSize: 12)),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),

        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => showDialog(context: context, builder: (_) => const LanguageSelectorDialog()),
                icon: const Icon(Icons.language, size: 16),
                label: AutoTranslatedText('🌐 Language', style: TextStyle(fontSize: 12)),
                style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 10)),
              ),
            ),
          ],
        ),
        const SizedBox(height: 20),

        if (RoleTabs.hasWallet(role)) ...[
          Consumer<PaymentProvider>(
            builder: (_, payments, __) => InkWell(
              onTap: () => Navigator.of(context).push<void>(
                MaterialPageRoute(builder: (_) => const WalletScreen(asTab: false)),
              ),
              borderRadius: BorderRadius.circular(20),
              child: Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(color: AppTheme.borderLight),
                ),
                child: Row(
                  children: [
                    AutoTranslatedText('👛', style: TextStyle(fontSize: 24)),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          AutoTranslatedText(
                            formatRupees(payments.walletBalance),
                            style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
                          ),
                          AutoTranslatedText(
                            '🔒 ${formatRupeesShort(payments.moneyInEscrow)} in escrow  •  ✅ ${formatRupeesShort(payments.lifetimeSettled)} settled',
                            style: const TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
                          ),
                        ],
                      ),
                    ),
                    AutoTranslatedText('➜', style: TextStyle(fontSize: 18, color: AppTheme.textMuted)),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
        ],

        if (isLogistics) ...[
          Consumer<LogisticsProvider>(
            builder: (_, logistics, __) => Row(
              children: [
                Expanded(
                  child: SymbolStat(
                    symbol: '✅',
                    value: '${logistics.completedTrips.length}',
                    caption: 'Trips done',
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SymbolStat(
                    symbol: '🛣️',
                    value: '${logistics.kmCovered.round()}',
                    caption: 'km covered',
                    color: AppTheme.accentTeal,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: SymbolStat(
                    symbol: '💰',
                    value: formatRupeesShort(logistics.earningsPaid),
                    caption: 'Earned',
                    color: AppTheme.accentAmber,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),
        ],

        if (auth.isLoggedIn) ...[
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              if (isFarmer) ...[
                _buildTabButton('deals', '🤝 Offers (${_deals.length})', activeTab),
                _buildTabButton('sales', '🧾 Sales', activeTab),
              ],
              if (isBuyer) ...[
                _buildTabButton('buyer_bids', '⚖️ My Bids', activeTab),
                _buildTabButton('buyer_purchases', '🔒 Escrow', activeTab),
              ],
              _buildTabButton('kyc', '✅ KYC', activeTab),
            ],
          ),
          const SizedBox(height: 14),
        ],

        if (isFarmer && activeTab == 'deals') ...[
          ..._deals.asMap().entries.map((entry) {
            final idx = entry.key;
            final deal = entry.value;
            final isPending = deal.status == 'pending';

            return Container(
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppTheme.borderLight),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Row(
                        children: [
                          AutoTranslatedText(deal.cropEmoji, style: const TextStyle(fontSize: 22)),
                          const SizedBox(width: 8),
                          AutoTranslatedText(deal.cropName, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                        ],
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        decoration: BoxDecoration(
                          color: isPending ? const Color(0xFFFEF3C7) : const Color(0xFFDCFCE7),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: AutoTranslatedText(
                          deal.status.toUpperCase(),
                          style: TextStyle(
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                            color: isPending ? const Color(0xFF92400E) : AppTheme.primaryGreen,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 6),
                  AutoTranslatedText('${deal.buyerCompany} (${deal.buyerName})', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                  AutoTranslatedText('${deal.quantity.toInt()} ${deal.unit} • ₹${deal.bidPrice.toInt()}/unit', style: const TextStyle(fontSize: 11.5, color: AppTheme.textMuted)),
                  const Divider(height: 16),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      AutoTranslatedText('Total Contract: ₹${deal.totalAmount.toInt()}', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
                      if (isPending)
                        Row(
                          children: [
                            TextButton(
                              onPressed: () => _declineDeal(idx),
                              child: AutoTranslatedText('Decline', style: TextStyle(color: Colors.red, fontSize: 12)),
                            ),
                            const SizedBox(width: 4),
                            ElevatedButton(
                              onPressed: () => _acceptDeal(idx),
                              style: ElevatedButton.styleFrom(
                                minimumSize: const Size(0, 34),
                                padding: const EdgeInsets.symmetric(horizontal: 12),
                              ),
                              child: AutoTranslatedText('Accept Offer', style: TextStyle(fontSize: 12)),
                            ),
                          ],
                        )
                      else
                        AutoTranslatedText('Token Held in Escrow ✓', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppTheme.primaryGreen)),
                    ],
                  ),
                ],
              ),
            );
          }),
        ],

        if (isFarmer && activeTab == 'sales') ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText('Settled Mandi Receipts (गत विक्री पावत्या)', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                SizedBox(height: 10),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(backgroundColor: Color(0xFFDCFCE7), child: Icon(Icons.check, color: AppTheme.primaryGreen)),
                  title: AutoTranslatedText('Sharbati Wheat - 150 Quintals', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                  subtitle: AutoTranslatedText('Indore Mandi • Receipt #FNX-88192 • Settled', style: TextStyle(fontSize: 11)),
                  trailing: AutoTranslatedText('₹3,67,500', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
                ),
                Divider(),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(backgroundColor: Color(0xFFDCFCE7), child: Icon(Icons.check, color: AppTheme.primaryGreen)),
                  title: AutoTranslatedText('Yellow Soybean - 80 Quintals', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                  subtitle: AutoTranslatedText('Latur Mandi • Receipt #FNX-77102 • Settled', style: TextStyle(fontSize: 11)),
                  trailing: AutoTranslatedText('₹3,88,000', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
                ),
              ],
            ),
          ),
        ],

        if (activeTab == 'kyc' && auth.isLoggedIn) ...[
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText('KYC documents', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w900)),
                const SizedBox(height: 6),
                AutoTranslatedText('Upload only ${role.displayName} documents from this account.', style: const TextStyle(fontSize: 11.5, color: AppTheme.textMuted)),
                const SizedBox(height: 14),
                ElevatedButton.icon(
                  onPressed: () => showDialog(context: context, builder: (_) => const VerificationDialog()),
                  icon: const Icon(Icons.upload_file),
                  label: AutoTranslatedText('Upload KYC document'),
                ),
              ],
            ),
          ),
        ],

        if (isBuyer && activeTab == 'buyer_bids') ...[
          const SizedBox(
            height: 620,
            child: BuyerBidsScreen(),
          ),
        ],

        if (isBuyer && activeTab == 'buyer_purchases') ...[
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: AppTheme.borderLight),
            ),
            child: const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                AutoTranslatedText('Escrow Contracts (एस्क्रो सुरक्षित खरेदी)', style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                SizedBox(height: 10),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: CircleAvatar(backgroundColor: Color(0xFFFEF3C7), child: Icon(Icons.lock, color: Color(0xFFD97706))),
                  title: AutoTranslatedText('Sharbati Wheat - 100 Quintals', style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold)),
                  subtitle: AutoTranslatedText('Ramesh Patil • Trk #TRK-9821 • Escrow Deposited', style: TextStyle(fontSize: 11)),
                  trailing: AutoTranslatedText('₹2,45,000', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w900, color: AppTheme.primaryGreen)),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildTabButton(String id, String label, String activeTab) {
    final isSelected = activeTab == id;
    return ChoiceChip(
      label: AutoTranslatedText(label, style: const TextStyle(fontSize: 12)),
      selected: isSelected,
      onSelected: (_) => setState(() => _activeTab = id),
      selectedColor: AppTheme.primaryGreen.withValues(alpha: 0.15),
      labelStyle: TextStyle(
        fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
        color: isSelected ? AppTheme.primaryGreen : AppTheme.textDark,
      ),
    );
  }
}
