import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';

class CropMediaItem {
  final String id;
  final String cropId;
  final String cropName;
  final String farmerName;
  final String name;
  final List<int>? bytes;
  final String? path;
  final bool isVideo;

  const CropMediaItem({
    required this.id,
    required this.cropId,
    required this.cropName,
    required this.farmerName,
    required this.name,
    this.bytes,
    this.path,
    required this.isVideo,
  });
}

class CropMediaProvider extends ChangeNotifier {
  final Map<String, List<CropMediaItem>> _media = {};

  List<CropMediaItem> forCrop(String cropId) => List.unmodifiable(_media[cropId] ?? const []);

  void addFiles({
    required String cropId,
    required String cropName,
    required String farmerName,
    required List<PlatformFile> files,
  }) {
    final list = _media.putIfAbsent(cropId, () => <CropMediaItem>[]);
    for (final file in files) {
      final ext = (file.extension ?? '').toLowerCase();
      final isVideo = {'mp4', 'mov', 'm4v', 'avi', 'webm', 'mkv'}.contains(ext);
      list.insert(
        0,
        CropMediaItem(
          id: '${cropId}-${DateTime.now().microsecondsSinceEpoch}-${file.name}',
          cropId: cropId,
          cropName: cropName,
          farmerName: farmerName,
          name: file.name,
          bytes: file.bytes,
          path: file.path,
          isVideo: isVideo,
        ),
      );
    }
    notifyListeners();
  }
}
