import 'dart:async';
import 'package:flutter/material.dart';
import 'auto_translated_text.dart';
import '../core/theme/app_theme.dart';

class PromoBanner {
  final String title;
  final String subtitle;
  final IconData icon;
  final List<Color> gradient;
  const PromoBanner({required this.title, required this.subtitle, required this.icon, required this.gradient});
}

class PromoBannerCarousel extends StatefulWidget {
  final List<PromoBanner>? banners;
  const PromoBannerCarousel({super.key, this.banners});

  static const List<PromoBanner> _defaultBanners = [
    PromoBanner(title: 'Fresh produce offers', subtitle: 'Explore current farmer listings and market prices.', icon: Icons.shopping_basket_outlined, gradient: [Color(0xFF0B6B3A), Color(0xFF16864B)]),
    PromoBanner(title: 'Direct farmer marketplace', subtitle: 'Compare lots, view crop media and buy direct.', icon: Icons.storefront_outlined, gradient: [Color(0xFF0E7490), Color(0xFF0F766E)]),
    PromoBanner(title: 'Mandi price intelligence', subtitle: 'Track price movement before you make a decision.', icon: Icons.trending_up_rounded, gradient: [Color(0xFF8A5A00), Color(0xFFB7791F)]),
  ];

  @override
  State<PromoBannerCarousel> createState() => _PromoBannerCarouselState();
}

class _PromoBannerCarouselState extends State<PromoBannerCarousel> {
  final PageController _controller = PageController();
  Timer? _timer;
  int _index = 0;

  List<PromoBanner> get _banners => widget.banners ?? PromoBannerCarousel._defaultBanners;

  @override
  void initState() {
    super.initState();
    _timer = Timer.periodic(const Duration(seconds: 4), (_) {
      if (!mounted || _banners.length < 2) return;
      _index = (_index + 1) % _banners.length;
      _controller.animateToPage(_index, duration: const Duration(milliseconds: 380), curve: Curves.easeInOut);
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          height: 104,
          child: PageView.builder(
            controller: _controller,
            itemCount: _banners.length,
            onPageChanged: (i) => setState(() => _index = i),
            itemBuilder: (_, i) {
              final banner = _banners[i];
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 1),
                padding: const EdgeInsets.all(15),
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: banner.gradient),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(color: Colors.white.withValues(alpha: .16), borderRadius: BorderRadius.circular(11)),
                      child: Icon(banner.icon, color: Colors.white, size: 24),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          AutoTranslatedText(banner.title, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w900)),
                          const SizedBox(height: 3),
                          AutoTranslatedText(banner.subtitle, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: Colors.white.withValues(alpha: .92), fontSize: 10.5, height: 1.25)),
                        ],
                      ),
                    ),
                  ],
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 7),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(_banners.length, (i) {
            return AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              margin: const EdgeInsets.symmetric(horizontal: 3),
              width: i == _index ? 15 : 6,
              height: 5,
              decoration: BoxDecoration(color: i == _index ? AppTheme.primaryGreen : AppTheme.borderLight, borderRadius: BorderRadius.circular(3)),
            );
          }),
        ),
      ],
    );
  }
}
