import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../config/api_config.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  StreamController<Map<String, dynamic>>? _streamController;
  Timer? _reconnectTimer;
  String? _currentCropId;
  bool _isDisposed = false;

  Stream<Map<String, dynamic>> connectToCropBids(String cropId) {
    _currentCropId = cropId;
    _streamController?.close();
    _streamController = StreamController<Map<String, dynamic>>.broadcast();
    _connect(cropId);
    return _streamController!.stream;
  }

  void _connect(String cropId) {
    if (_isDisposed) return;
    try {
      final wsUri = Uri.parse(ApiConfig.cropBidsWsUrl(cropId));
      _channel = WebSocketChannel.connect(wsUri);

      _channel!.stream.listen(
        (event) {
          try {
            final data = jsonDecode(event.toString()) as Map<String, dynamic>;
            _streamController?.add(data);
          } catch (_) {}
        },
        onError: (error) {
          _scheduleReconnect(cropId);
        },
        onDone: () {
          _scheduleReconnect(cropId);
        },
        cancelOnError: false,
      );
    } catch (_) {
      _scheduleReconnect(cropId);
    }
  }

  void _scheduleReconnect(String cropId) {
    if (_isDisposed) return;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), () {
      if (!_isDisposed && _currentCropId == cropId) {
        _connect(cropId);
      }
    });
  }

  void sendBid(Map<String, dynamic> bidData) {
    try {
      _channel?.sink.add(jsonEncode(bidData));
    } catch (_) {}
  }

  void disconnect() {
    _isDisposed = true;
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _streamController?.close();
  }
}
