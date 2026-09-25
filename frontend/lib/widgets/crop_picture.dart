import 'package:flutter/material.dart';
import 'auto_translated_text.dart';

class CropPicture extends StatelessWidget {
  final String cropName;
  final String fallbackEmoji;
  final double size;
  final BorderRadius borderRadius;

  const CropPicture({
    super.key,
    required this.cropName,
    required this.fallbackEmoji,
    this.size = 64,
    this.borderRadius = const BorderRadius.all(Radius.circular(14)),
  });

  String? get _asset {
    final name = cropName.toLowerCase();
    if (name.contains('tomato')) return 'assets/farm/tomato.png';
    if (name.contains('onion')) return 'assets/farm/onion.png';
    if (name.contains('wheat')) return 'assets/farm/wheat.png';
    return null;
  }

  @override
  Widget build(BuildContext context) {
    final asset = _asset;
    if (asset == null) {
      return Container(
        width: size,
        height: size,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: const Color(0xFFF9FAFB),
          borderRadius: borderRadius,
        ),
        child: AutoTranslatedText(fallbackEmoji, style: TextStyle(fontSize: size * 0.42)),
      );
    }

    return ClipRRect(
      borderRadius: borderRadius,
      child: Image.asset(
        asset,
        width: size,
        height: size,
        fit: BoxFit.cover,
        filterQuality: FilterQuality.high,
        errorBuilder: (_, __, ___) => Container(
          width: size,
          height: size,
          color: const Color(0xFFF9FAFB),
          alignment: Alignment.center,
          child: AutoTranslatedText(fallbackEmoji, style: TextStyle(fontSize: size * 0.42)),
        ),
      ),
    );
  }
}
