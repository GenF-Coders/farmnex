import 'package:farmnex_flutter/models/listing_model.dart';
import 'package:farmnex_flutter/models/rescue_listing_model.dart';
import 'package:farmnex_flutter/screens/rescue/crop_rescue_screen.dart';
import 'package:flutter_test/flutter_test.dart';

Map<String, dynamic> _listing({String? lotId, String? note}) => {
      'public_id': 'l-1',
      'seller_id': 's-1',
      'farm_id': 'f-1',
      'crop_batch_id': 'b-1',
      'title': 'Tomato',
      'listing_type': 'FIXED_PRICE',
      'price': '24',
      'quantity': '500',
      'available_quantity': '500',
      'unit': 'kg',
      'status': 'ACTIVE',
      'rescue_lot_id': lotId,
      'rescue_note': note,
    };

Map<String, dynamic> _lot({required bool estimate, double hours = 60}) => {
      'id': 'lot-1',
      'crop_code': estimate ? 'wheat' : 'tomato',
      'quantity_kg': 500,
      'storage_mode': 'ambient',
      'floor_price_per_kg': 24,
      'remaining_hours': hours,
      'status': 'FRESH',
      'estimate': estimate,
    };

void main() {
  test('a new listing carries the Crop Rescue timer result', () {
    final started = ListingModel.fromJson(_listing(lotId: 'lot-1'));
    expect(started.rescueLotId, 'lot-1');
    expect(started.rescueNote, isNull);

    final skipped = ListingModel.fromJson(_listing(note: 'Add your farm location'));
    expect(skipped.rescueLotId, isNull);
    expect(skipped.rescueNote, 'Add your farm location');
  });

  test('older replies without the rescue fields still parse', () {
    final json = _listing()
      ..remove('rescue_lot_id')
      ..remove('rescue_note');
    expect(ListingModel.fromJson(json).rescueLotId, isNull);
  });

  test('estimated shelf lives are labelled, researched ones are not', () {
    expect(rescueTimeLeft(RescueLot.fromJson(_lot(estimate: false))), '2 days 12 h left');
    expect(rescueTimeLeft(RescueLot.fromJson(_lot(estimate: true))), '2 days 12 h left (estimate)');
    expect(rescueTimeLeft(RescueLot.fromJson(_lot(estimate: true, hours: 5))), '5 h left (estimate)');
    expect(RescueCrop.fromJson({'code': 'wheat', 'estimate': true}).estimate, isTrue);
    expect(RescueCrop.fromJson({'code': 'tomato'}).estimate, isFalse);
  });
}
