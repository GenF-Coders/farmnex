// Lot photos/videos and the "Verified by FarmNex" status, exactly as
// `/api/v2/product-listings/{id}/media` and `/api/v2/admin/listing-verifications` return them.

DateTime? _time(dynamic v) => v == null ? null : DateTime.tryParse(v.toString())?.toLocal();

class ListingMediaItem {
  final String id;

  /// `PHOTO` or `VIDEO`.
  final String kind;
  final String contentType;
  final int sizeBytes;

  /// Short-lived signed link (about 15 minutes); null if storage was briefly unavailable.
  final String? url;

  const ListingMediaItem({
    required this.id,
    required this.kind,
    required this.contentType,
    required this.sizeBytes,
    required this.url,
  });

  bool get isVideo => kind == 'VIDEO';

  factory ListingMediaItem.fromJson(Map<String, dynamic> json) => ListingMediaItem(
        id: json['public_id'].toString(),
        kind: (json['kind'] ?? 'PHOTO').toString(),
        contentType: (json['content_type'] ?? '').toString(),
        sizeBytes: (json['size_bytes'] as num?)?.toInt() ?? 0,
        url: json['url'] as String?,
      );
}

class ListingMedia {
  final String listingId;

  /// `NONE` (no photos yet), `PENDING` (waiting for FarmNex), `VERIFIED` or `REJECTED`.
  final String status;
  final String? reason;
  final List<ListingMediaItem> items;
  final int maxPhotos;
  final int maxVideos;

  const ListingMedia({
    required this.listingId,
    required this.status,
    required this.reason,
    required this.items,
    required this.maxPhotos,
    required this.maxVideos,
  });

  bool get isVerified => status == 'VERIFIED';
  int get photoCount => items.where((i) => !i.isVideo).length;
  int get videoCount => items.where((i) => i.isVideo).length;

  factory ListingMedia.fromJson(Map<String, dynamic> json) {
    final verification = (json['verification'] as Map<String, dynamic>?) ?? const {};
    return ListingMedia(
      listingId: json['listing_id'].toString(),
      status: (verification['status'] ?? 'NONE').toString(),
      reason: verification['reason'] as String?,
      items: ((json['items'] as List<dynamic>?) ?? const [])
          .map((e) => ListingMediaItem.fromJson(e as Map<String, dynamic>))
          .toList(),
      maxPhotos: (json['max_photos'] as num?)?.toInt() ?? 6,
      maxVideos: (json['max_videos'] as num?)?.toInt() ?? 2,
    );
  }
}

/// One row of the admin "Verify lots" queue.
class VerificationQueueItem {
  final String listingId;
  final String title;
  final String listingType;
  final double price;
  final String unit;
  final String status;
  final String? reason;
  final int mediaCount;
  final DateTime? updatedAt;

  const VerificationQueueItem({
    required this.listingId,
    required this.title,
    required this.listingType,
    required this.price,
    required this.unit,
    required this.status,
    required this.reason,
    required this.mediaCount,
    required this.updatedAt,
  });

  factory VerificationQueueItem.fromJson(Map<String, dynamic> json) => VerificationQueueItem(
        listingId: json['listing_id'].toString(),
        title: (json['title'] ?? '').toString(),
        listingType: (json['listing_type'] ?? '').toString(),
        price: double.tryParse('${json['price']}') ?? 0,
        unit: (json['unit'] ?? '').toString(),
        status: (json['status'] ?? 'PENDING').toString(),
        reason: json['reason'] as String?,
        mediaCount: (json['media_count'] as num?)?.toInt() ?? 0,
        updatedAt: _time(json['updated_at']),
      );
}
