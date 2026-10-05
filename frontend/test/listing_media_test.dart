import 'package:farmnex_flutter/core/network/listing_media_api.dart';
import 'package:farmnex_flutter/localization/language_provider.dart';
import 'package:farmnex_flutter/models/listing_media_model.dart';
import 'package:farmnex_flutter/models/listing_model.dart';
import 'package:farmnex_flutter/widgets/listing_media_section.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('media reply parses items, limits and the verification status', () {
    final media = ListingMedia.fromJson({
      'listing_id': 'l-1',
      'verification': {'status': 'REJECTED', 'reason': 'Photo is blurry'},
      'items': [
        {'public_id': 'm-1', 'kind': 'PHOTO', 'content_type': 'image/jpeg', 'size_bytes': 1200, 'url': 'https://x/1'},
        {'public_id': 'm-2', 'kind': 'VIDEO', 'content_type': 'video/mp4', 'size_bytes': 9000, 'url': null},
      ],
      'max_photos': 6,
      'max_videos': 2,
    });
    expect((media.status, media.reason, media.isVerified), ('REJECTED', 'Photo is blurry', false));
    expect((media.photoCount, media.videoCount), (1, 1));
    expect(media.items.last.isVideo, isTrue);
    expect(media.items.last.url, isNull);
  });

  test('listings carry the FarmNex badge to the market card', () {
    final json = {
      'public_id': 'l-1', 'seller_id': 's-1', 'farm_id': 'f-1', 'crop_batch_id': 'b-1', 'title': 'Tomato',
      'listing_type': 'FIXED_PRICE', 'price': '24', 'quantity': '5', 'available_quantity': '5', 'unit': 'kg',
      'status': 'ACTIVE', 'verification_status': 'VERIFIED', 'media_count': 3,
    };
    final listing = ListingModel.fromJson(json);
    expect((listing.verificationStatus, listing.mediaCount), ('VERIFIED', 3));
    expect(listing.toCropItem().verificationStatus, 'VERIFIED');

    final older = ListingModel.fromJson(json..remove('verification_status')..remove('media_count'));
    expect(older.toCropItem().verificationStatus, 'NONE');
  });

  test('camera file names map to the types the server accepts', () {
    expect(mediaContentType('IMG_1.JPG'), 'image/jpeg');
    expect(mediaContentType('clip.mov'), 'video/quicktime');
    expect(mediaContentType('clip.mp4'), 'video/mp4');
    expect(mediaContentType('notes.pdf'), isNull);
  });

  testWidgets('badge shows the verified label', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(ChangeNotifierProvider(
      create: (_) => LanguageProvider(),
      child: const MaterialApp(home: Scaffold(body: VerificationBadge(status: 'VERIFIED'))),
    ));
    await tester.pump();
    expect(find.textContaining('Verified by FarmNex'), findsOneWidget);
  });
}
