import 'package:flutter/material.dart';

import '../../models/user_model.dart';
import '../../screens/admin/admin_screens.dart';
import '../../screens/bidding/pre_bidding_screen.dart';
import '../../screens/buyer/buyer_orders_screen.dart';
import '../../screens/buyer/cart_screen.dart';
import '../../screens/farmer/my_crops_screen.dart';
import '../../screens/home/home_screen.dart';
import '../../screens/logistics/logistics_screens.dart';
import '../../screens/market/market_screen.dart';
import '../../screens/profile/profile_screen.dart';
import '../../screens/rescue/crop_rescue_screen.dart';

typedef TabNavigator = void Function(String tabId);

class AppTab {

  final String id;

  final String symbol;

  final IconData icon;
  final IconData activeIcon;

  final String labelKey;

  final String fallbackLabel;

  final Widget Function(BuildContext context, TabNavigator go) builder;

  const AppTab({
    required this.id,
    required this.symbol,
    required this.icon,
    required this.activeIcon,
    required this.labelKey,
    required this.fallbackLabel,
    required this.builder,
  });
}

class RoleTabs {
  const RoleTabs._();

  static List<AppTab> forRole(UserRole role) {
    switch (role) {
      case UserRole.farmer:
        return _farmer;
      case UserRole.buyer:
        return _buyer;
      case UserRole.logistics:
        return _logistics;
      case UserRole.admin:
        return _admin;
      case UserRole.guest:
        return _guest;
    }
  }

  static String badgeFor(UserRole role) {
    switch (role) {
      case UserRole.farmer:
        return '🧑‍🌾 Farmer';
      case UserRole.buyer:
        return '🏢 Buyer';
      case UserRole.logistics:
        return '🚚 Transport';
      case UserRole.admin:
        return '🛡️ APMC';
      case UserRole.guest:
        return '👀 Guest';
    }
  }

  static String symbolFor(UserRole role) {
    switch (role) {
      case UserRole.farmer:
        return '🧑‍🌾';
      case UserRole.buyer:
        return '🏢';
      case UserRole.logistics:
        return '🚚';
      case UserRole.admin:
        return '🛡️';
      case UserRole.guest:
        return '👀';
    }
  }

  static bool hasWallet(UserRole role) =>
      role == UserRole.farmer || role == UserRole.buyer || role == UserRole.logistics;

  static bool hasCart(UserRole role) => role == UserRole.buyer;

  static final List<AppTab> _guest = [
    AppTab(
      id: 'home',
      symbol: '🏠',
      icon: Icons.home_outlined,
      activeIcon: Icons.home,
      labelKey: 'home',
      fallbackLabel: 'Home',
      builder: (_, go) => HomeScreen(onNavigateTab: go),
    ),
    AppTab(
      id: 'market',
      symbol: '🏪',
      icon: Icons.storefront_outlined,
      activeIcon: Icons.storefront,
      labelKey: 'market',
      fallbackLabel: 'Mandi',
      builder: (_, __) => const MarketScreen(),
    ),
    AppTab(
      id: 'rescue',
      symbol: '🚨',
      icon: Icons.bolt_outlined,
      activeIcon: Icons.bolt,
      labelKey: 'rescue',
      fallbackLabel: 'Rescue',
      builder: (_, __) => const CropRescueScreen(),
    ),
    AppTab(
      id: 'prebid',
      symbol: '⏳',
      icon: Icons.schedule_outlined,
      activeIcon: Icons.schedule,
      labelKey: 'prebid',
      fallbackLabel: 'Pre-Bid',
      builder: (_, __) => const PreBiddingScreen(),
    ),
    AppTab(
      id: 'profile',
      symbol: '🔐',
      icon: Icons.login_outlined,
      activeIcon: Icons.login,
      labelKey: 'login',
      fallbackLabel: 'Login',
      builder: (_, __) => const ProfileScreen(),
    ),
  ];

  static final List<AppTab> _farmer = [
    AppTab(
      id: 'home',
      symbol: '🏠',
      icon: Icons.home_outlined,
      activeIcon: Icons.home,
      labelKey: 'home',
      fallbackLabel: 'Home',
      builder: (_, go) => HomeScreen(onNavigateTab: go),
    ),
    AppTab(
      id: 'my_crops',
      symbol: '🌾',
      icon: Icons.grass_outlined,
      activeIcon: Icons.grass,
      labelKey: 'my_crops',
      fallbackLabel: 'My Crops',
      builder: (_, __) => const MyCropsScreen(),
    ),
    AppTab(
      id: 'prebid',
      symbol: '⏳',
      icon: Icons.schedule_outlined,
      activeIcon: Icons.schedule,
      labelKey: 'prebid',
      fallbackLabel: 'Pre-Bid',
      builder: (_, __) => const PreBiddingScreen(),
    ),
    AppTab(
      id: 'rescue',
      symbol: '🚨',
      icon: Icons.warning_amber_outlined,
      activeIcon: Icons.warning,
      labelKey: 'rescue',
      fallbackLabel: 'Rescue',
      builder: (_, __) => const CropRescueScreen(),
    ),
    AppTab(
      id: 'profile',
      symbol: '👤',
      icon: Icons.person_outline,
      activeIcon: Icons.person,
      labelKey: 'profile',
      fallbackLabel: 'Profile',
      builder: (_, __) => const ProfileScreen(),
    ),
  ];

  static final List<AppTab> _buyer = [
    AppTab(
      id: 'market',
      symbol: '🏪',
      icon: Icons.storefront_outlined,
      activeIcon: Icons.storefront,
      labelKey: 'market',
      fallbackLabel: 'Mandi',
      builder: (_, __) => const MarketScreen(),
    ),

    AppTab(
      id: 'rescue',
      symbol: '🚨',
      icon: Icons.bolt_outlined,
      activeIcon: Icons.bolt,
      labelKey: 'rescue',
      fallbackLabel: 'Rescue',
      builder: (_, __) => const CropRescueScreen(),
    ),
    AppTab(
      id: 'cart',
      symbol: '🛒',
      icon: Icons.shopping_cart_outlined,
      activeIcon: Icons.shopping_cart,
      labelKey: 'cart',
      fallbackLabel: 'Cart',
      builder: (_, go) => CartScreen(onBrowse: () => go('market')),
    ),
    AppTab(
      id: 'orders',
      symbol: '📦',
      icon: Icons.inventory_2_outlined,
      activeIcon: Icons.inventory_2,
      labelKey: 'orders',
      fallbackLabel: 'Orders',
      builder: (_, go) => BuyerOrdersScreen(onBrowse: () => go('market')),
    ),
    AppTab(
      id: 'profile',
      symbol: '👤',
      icon: Icons.person_outline,
      activeIcon: Icons.person,
      labelKey: 'profile',
      fallbackLabel: 'Profile',
      builder: (_, __) => const ProfileScreen(),
    ),
  ];

  static final List<AppTab> _logistics = [
    AppTab(
      id: 'loads',
      symbol: '📋',
      icon: Icons.assignment_outlined,
      activeIcon: Icons.assignment,
      labelKey: 'loads',
      fallbackLabel: 'Loads',
      builder: (_, __) => const LogisticsLoadsScreen(),
    ),
    AppTab(
      id: 'active',
      symbol: '🚚',
      icon: Icons.local_shipping_outlined,
      activeIcon: Icons.local_shipping,
      labelKey: 'active_trips',
      fallbackLabel: 'Trips',
      builder: (_, __) => const LogisticsActiveScreen(),
    ),
    AppTab(
      id: 'earnings',
      symbol: '💰',
      icon: Icons.account_balance_wallet_outlined,
      activeIcon: Icons.account_balance_wallet,
      labelKey: 'earnings',
      fallbackLabel: 'Earnings',
      builder: (_, __) => const LogisticsEarningsScreen(),
    ),
    AppTab(
      id: 'profile',
      symbol: '👤',
      icon: Icons.person_outline,
      activeIcon: Icons.person,
      labelKey: 'profile',
      fallbackLabel: 'Profile',
      builder: (_, __) => const ProfileScreen(),
    ),
  ];

  static final List<AppTab> _admin = [
    AppTab(
      id: 'admin_home',
      symbol: '📊',
      icon: Icons.dashboard_outlined,
      activeIcon: Icons.dashboard,
      labelKey: 'dashboard',
      fallbackLabel: 'Console',
      builder: (_, go) => AdminDashboardScreen(onNavigate: go),
    ),
    AppTab(
      id: 'admin_kyc',
      symbol: '✅',
      icon: Icons.verified_user_outlined,
      activeIcon: Icons.verified_user,
      labelKey: 'kyc',
      fallbackLabel: 'KYC',
      builder: (_, __) => const AdminKycScreen(),
    ),
    AppTab(
      id: 'admin_users',
      symbol: '👥',
      icon: Icons.groups_outlined,
      activeIcon: Icons.groups,
      labelKey: 'users',
      fallbackLabel: 'Users',
      builder: (_, __) => const AdminUsersScreen(),
    ),
    AppTab(
      id: 'admin_money',
      symbol: '💳',
      icon: Icons.payments_outlined,
      activeIcon: Icons.payments,
      labelKey: 'payments',
      fallbackLabel: 'Money',
      builder: (_, __) => const AdminMoneyScreen(),
    ),
    AppTab(
      id: 'profile',
      symbol: '👤',
      icon: Icons.person_outline,
      activeIcon: Icons.person,
      labelKey: 'profile',
      fallbackLabel: 'Profile',
      builder: (_, __) => const ProfileScreen(),
    ),
  ];
}
