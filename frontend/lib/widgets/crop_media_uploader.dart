import 'auto_translated_text.dart';
import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../core/theme/app_theme.dart';
import '../models/user_model.dart';
import '../providers/auth_provider.dart';
import '../providers/crop_media_provider.dart';

class CropMediaUploader extends StatelessWidget {
  final String cropId;
  final String cropName;
  final String? farmerName;

  const CropMediaUploader({
    super.key,
    required this.cropId,
    required this.cropName,
    this.farmerName,
  });

  Future<void> _pick(BuildContext context) async {
    final auth = context.read<AuthProvider>();
    if (!auth.isLoggedIn || auth.user?.role != UserRole.farmer) return;
    final result = await FilePicker.platform.pickFiles(
      allowMultiple: true,
      type: FileType.custom,
      allowedExtensions: const ['jpg', 'jpeg', 'png', 'webp', 'mp4', 'mov', 'm4v', 'avi', 'webm'],
      withData: true,
    );
    if (result == null || result.files.isEmpty || !context.mounted) return;

    context.read<CropMediaProvider>().addFiles(
          cropId: cropId,
          cropName: cropName,
          farmerName: farmerName ?? auth.user?.name ?? 'Farmer',
          files: result.files,
        );
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: AutoTranslatedText('${result.files.length} crop media file(s) added.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.isLoggedIn || auth.user?.role != UserRole.farmer) return const SizedBox.shrink();
    return OutlinedButton.icon(
      onPressed: () => _pick(context),
      icon: const Icon(Icons.add_photo_alternate_outlined, size: 17),
      label: AutoTranslatedText('Upload crop photo / video'),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppTheme.primaryGreen,
        side: const BorderSide(color: AppTheme.primaryGreen),
        minimumSize: const Size(0, 38),
      ),
    );
  }
}

class CropMediaGallery extends StatelessWidget {
  final String cropId;
  const CropMediaGallery({super.key, required this.cropId});

  @override
  Widget build(BuildContext context) {
    final media = context.watch<CropMediaProvider>().forCrop(cropId);
    if (media.isEmpty) return const SizedBox.shrink();
    return Container(
      margin: const EdgeInsets.only(top: 10),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: const Color(0xFFF9FAFB),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppTheme.borderLight),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          AutoTranslatedText('Crop photos & videos', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          SizedBox(
            height: 86,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: media.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (_, i) => _MediaThumb(item: media[i]),
            ),
          ),
        ],
      ),
    );
  }
}

class _MediaThumb extends StatelessWidget {
  final CropMediaItem item;
  const _MediaThumb({required this.item});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => showDialog<void>(
        context: context,
        builder: (_) => _MediaPreview(item: item),
      ),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 104,
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppTheme.borderLight),
        ),
        clipBehavior: Clip.antiAlias,
        child: item.isVideo
            ? const Stack(
                alignment: Alignment.center,
                children: [
                  Icon(Icons.video_library_outlined, size: 34, color: AppTheme.primaryGreen),
                  Positioned(bottom: 5, child: Icon(Icons.play_circle_fill, size: 20, color: AppTheme.primaryGreen)),
                ],
              )
            : item.bytes != null
                ? Image.memory(Uint8List.fromList(item.bytes!), fit: BoxFit.cover)
                : const Icon(Icons.image_outlined, size: 32, color: AppTheme.primaryGreen),
      ),
    );
  }
}

class _MediaPreview extends StatelessWidget {
  final CropMediaItem item;
  const _MediaPreview({required this.item});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 700, maxHeight: 650),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Expanded(child: AutoTranslatedText(item.name, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800))),
                  IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.close)),
                ],
              ),
              const SizedBox(height: 8),
              Flexible(
                child: item.isVideo
                    ? Container(
                        height: 360,
                        width: double.infinity,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(color: Colors.black12, borderRadius: BorderRadius.circular(14)),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.play_circle_outline, size: 64, color: AppTheme.primaryGreen),
                            const SizedBox(height: 8),
                            AutoTranslatedText(item.name, textAlign: TextAlign.center),
                            const SizedBox(height: 4),
                            AutoTranslatedText('Video selected for this crop', style: TextStyle(color: AppTheme.textMuted, fontSize: 11)),
                          ],
                        ),
                      )
                    : item.bytes != null
                        ? InteractiveViewer(child: Image.memory(Uint8List.fromList(item.bytes!), fit: BoxFit.contain))
                        : const Icon(Icons.image_outlined, size: 80),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
