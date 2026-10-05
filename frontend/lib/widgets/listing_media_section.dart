import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:video_player/video_player.dart';

import '../core/network/listing_api.dart' show listingErrorMessage;
import '../core/network/listing_media_api.dart';
import '../core/theme/app_theme.dart';
import '../models/listing_media_model.dart';
import 'auto_translated_text.dart';

/// Biggest file the server takes (backend storage limit).
const int kMaxMediaBytes = 10 * 1024 * 1024;

/// "✅ Verified by FarmNex" and friends, for a lot's verification status.
class VerificationBadge extends StatelessWidget {
  final String status;
  final bool compact;

  const VerificationBadge({super.key, required this.status, this.compact = false});

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (status) {
      'VERIFIED' => (compact ? '✅ Verified' : '✅ Verified by FarmNex', AppTheme.primaryGreen),
      'PENDING' => ('⏳ Waiting for FarmNex check', AppTheme.accentAmber),
      'REJECTED' => ('❌ Not verified — see reason', AppTheme.alertRed),
      _ => ('📷 No photos yet', AppTheme.textMuted),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
      ),
      child: AutoTranslatedText(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: color)),
    );
  }
}

/// A lot's photos and videos with its verification status.
/// `canEdit` (the lot's own farmer) adds camera buttons and delete; everyone else only views.
class ListingMediaSection extends StatefulWidget {
  final String listingId;
  final bool canEdit;

  /// Called after the farmer adds or deletes something (e.g. to refresh a list).
  final VoidCallback? onChanged;

  const ListingMediaSection({super.key, required this.listingId, this.canEdit = false, this.onChanged});

  @override
  State<ListingMediaSection> createState() => _ListingMediaSectionState();
}

class _ListingMediaSectionState extends State<ListingMediaSection> {
  final _api = ListingMediaApi();
  ListingMedia? _media;
  String? _error;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final media = await _api.list(widget.listingId);
      if (mounted) {
        setState(() {
          _media = media;
          _error = null;
        });
      }
    } catch (e) {
      if (mounted) setState(() => _error = listingErrorMessage(e));
    }
  }

  Future<void> _capture({required bool video}) async {
    final messenger = ScaffoldMessenger.of(context);
    final picker = ImagePicker();
    final XFile? file;
    try {
      // Camera only: the farmer shows the crop as it is now.
      file = video
          ? await picker.pickVideo(source: ImageSource.camera, maxDuration: const Duration(seconds: 15))
          : await picker.pickImage(source: ImageSource.camera, maxWidth: 1600, imageQuality: 80);
    } catch (_) {
      messenger.showSnackBar(const SnackBar(content: AutoTranslatedText('⚠️ Could not open the camera.')));
      return;
    }
    if (file == null) return; // farmer cancelled
    final bytes = await file.readAsBytes();
    if (bytes.length > kMaxMediaBytes) {
      messenger.showSnackBar(
        const SnackBar(content: AutoTranslatedText('⚠️ The file is bigger than 10 MB. Record a shorter clip.')),
      );
      return;
    }
    final contentType = file.mimeType ?? mediaContentType(file.name) ?? (video ? 'video/mp4' : 'image/jpeg');
    setState(() => _busy = true);
    try {
      final media = await _api.upload(
        widget.listingId,
        bytes: bytes,
        filename: file.name.isEmpty ? (video ? 'lot.mp4' : 'lot.jpg') : file.name,
        contentType: contentType,
      );
      if (!mounted) return;
      setState(() => _media = media);
      widget.onChanged?.call();
      messenger.showSnackBar(SnackBar(
        content: AutoTranslatedText(video ? '✅ Video added. FarmNex will check it.' : '✅ Photo added. FarmNex will check it.'),
        backgroundColor: AppTheme.primaryGreen,
      ));
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: AutoTranslatedText('⚠️ ${_uploadError(e)}')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String _uploadError(Object e) {
    if (e is DioException && e.response?.statusCode == 503) {
      return 'Photo storage is busy. Please try again in a minute.';
    }
    return listingErrorMessage(e);
  }

  Future<void> _delete(ListingMediaItem item) async {
    final messenger = ScaffoldMessenger.of(context);
    final ok = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: AutoTranslatedText(item.isVideo ? 'Delete this video?' : 'Delete this photo?'),
        content: const AutoTranslatedText('The lot will need a new FarmNex check.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dialogContext, false), child: const AutoTranslatedText('Cancel')),
          TextButton(onPressed: () => Navigator.pop(dialogContext, true), child: const AutoTranslatedText('Delete')),
        ],
      ),
    );
    if (ok != true) return;
    setState(() => _busy = true);
    try {
      final media = await _api.delete(widget.listingId, item.id);
      if (!mounted) return;
      setState(() => _media = media);
      widget.onChanged?.call();
    } catch (e) {
      messenger.showSnackBar(SnackBar(content: AutoTranslatedText('⚠️ ${listingErrorMessage(e)}')));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final media = _media;
    if (media == null) {
      if (_error == null) {
        return const Padding(padding: EdgeInsets.all(12), child: Center(child: CircularProgressIndicator()));
      }
      // Viewers just don't see the section if it can't load; the farmer gets a retry.
      if (!widget.canEdit) return const SizedBox.shrink();
      return Row(children: [
        Expanded(child: AutoTranslatedText('⚠️ $_error', style: const TextStyle(fontSize: 12))),
        TextButton(onPressed: _load, child: const AutoTranslatedText('Try again')),
      ]);
    }
    if (!widget.canEdit && media.items.isEmpty) return const SizedBox.shrink();

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
          Row(children: [
            const Expanded(
              child: AutoTranslatedText('Crop photos & videos', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w800)),
            ),
            VerificationBadge(status: media.status, compact: !widget.canEdit),
          ]),
          if (widget.canEdit && media.status == 'REJECTED' && media.reason != null) ...[
            const SizedBox(height: 6),
            AutoTranslatedText('FarmNex: ${media.reason}', style: const TextStyle(fontSize: 12, color: AppTheme.alertRed)),
          ],
          if (media.items.isNotEmpty) ...[
            const SizedBox(height: 8),
            SizedBox(
              height: 86,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: media.items.length,
                separatorBuilder: (_, _) => const SizedBox(width: 8),
                itemBuilder: (_, i) => _Thumb(
                  item: media.items[i],
                  onDelete: widget.canEdit && !_busy ? () => _delete(media.items[i]) : null,
                ),
              ),
            ),
          ],
          if (widget.canEdit) ...[
            const SizedBox(height: 8),
            if (_busy)
              const LinearProgressIndicator()
            else
              Row(children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: media.photoCount < media.maxPhotos ? () => _capture(video: false) : null,
                    child: AutoTranslatedText('📷 Photo (${media.photoCount}/${media.maxPhotos})'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton(
                    onPressed: media.videoCount < media.maxVideos ? () => _capture(video: true) : null,
                    child: AutoTranslatedText('🎥 Video (${media.videoCount}/${media.maxVideos})'),
                  ),
                ),
              ]),
            const SizedBox(height: 4),
            const AutoTranslatedText(
              'Opens the camera. Videos up to 15 seconds. FarmNex checks new photos before the ✅ badge.',
              style: TextStyle(fontSize: 10.5, color: AppTheme.textMuted),
            ),
          ],
        ],
      ),
    );
  }
}

class _Thumb extends StatelessWidget {
  final ListingMediaItem item;
  final VoidCallback? onDelete;

  const _Thumb({required this.item, this.onDelete});

  @override
  Widget build(BuildContext context) {
    final url = item.url;
    return Stack(children: [
      InkWell(
        onTap: url == null ? null : () => showDialog<void>(context: context, builder: (_) => _Preview(item: item)),
        borderRadius: BorderRadius.circular(12),
        child: Container(
          width: 104,
          height: 86,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppTheme.borderLight),
          ),
          clipBehavior: Clip.antiAlias,
          child: item.isVideo || url == null
              ? Icon(item.isVideo ? Icons.play_circle_fill : Icons.image_outlined, size: 34, color: AppTheme.primaryGreen)
              : Image.network(
                  url,
                  fit: BoxFit.cover,
                  errorBuilder: (_, _, _) => const Icon(Icons.broken_image_outlined, color: AppTheme.textMuted),
                ),
        ),
      ),
      if (onDelete != null)
        Positioned(
          right: 2,
          top: 2,
          child: InkWell(
            onTap: onDelete,
            child: const CircleAvatar(radius: 11, backgroundColor: Colors.white, child: Icon(Icons.close, size: 14)),
          ),
        ),
    ]);
  }
}

class _Preview extends StatelessWidget {
  final ListingMediaItem item;
  const _Preview({required this.item});

  @override
  Widget build(BuildContext context) {
    return Dialog(
      insetPadding: const EdgeInsets.all(16),
      clipBehavior: Clip.antiAlias,
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        Flexible(
          child: item.isVideo
              ? _VideoPlayerView(url: item.url!)
              : InteractiveViewer(child: Image.network(item.url!, fit: BoxFit.contain)),
        ),
        TextButton(onPressed: () => Navigator.pop(context), child: const AutoTranslatedText('Close')),
      ]),
    );
  }
}

class _VideoPlayerView extends StatefulWidget {
  final String url;
  const _VideoPlayerView({required this.url});

  @override
  State<_VideoPlayerView> createState() => _VideoPlayerViewState();
}

class _VideoPlayerViewState extends State<_VideoPlayerView> {
  late final VideoPlayerController _controller = VideoPlayerController.networkUrl(Uri.parse(widget.url));
  bool _failed = false;

  @override
  void initState() {
    super.initState();
    _controller.initialize().then((_) {
      if (!mounted) return;
      setState(() {});
      _controller.play();
    }).catchError((Object _) {
      if (mounted) setState(() => _failed = true);
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_failed) {
      return const Padding(padding: EdgeInsets.all(24), child: AutoTranslatedText('⚠️ Could not play this video.'));
    }
    if (!_controller.value.isInitialized) {
      return const Padding(padding: EdgeInsets.all(32), child: CircularProgressIndicator());
    }
    return GestureDetector(
      onTap: () => setState(() => _controller.value.isPlaying ? _controller.pause() : _controller.play()),
      child: AspectRatio(aspectRatio: _controller.value.aspectRatio, child: VideoPlayer(_controller)),
    );
  }
}
