import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter_ai_bot/models/chat_message_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';

class WebSocketService {
  WebSocketChannel? _channel;
  StreamController<Map<String, dynamic>>? _messageController;
  Timer? _pingTimer;
  bool _isConnected = false;
  
  // Event streams
  Stream<ChatMessage>? _newMessageStream;
  Stream<Map<String, dynamic>>? _typingStream;
  Stream<List<Map<String, dynamic>>>? _onlineUsersStream;
  
  StreamController<ChatMessage>? _newMessageController;
  StreamController<Map<String, dynamic>>? _typingController;
  StreamController<List<Map<String, dynamic>>>? _onlineUsersController;

  WebSocketService() {
    _messageController = StreamController<Map<String, dynamic>>.broadcast();
    _newMessageController = StreamController<ChatMessage>.broadcast();
    _typingController = StreamController<Map<String, dynamic>>.broadcast();
    _onlineUsersController = StreamController<List<Map<String, dynamic>>>.broadcast();
    
    _newMessageStream = _newMessageController!.stream;
    _typingStream = _typingController!.stream;
    _onlineUsersStream = _onlineUsersController!.stream;
    
    _setupMessageHandling();
  }

  void _setupMessageHandling() {
    _messageController!.stream.listen((data) {
      final type = data['type'] as String?;
      
      switch (type) {
        case 'new_message':
          final messageData = data['message'] as Map<String, dynamic>;
          final message = ChatMessage.fromJson(messageData);
          _newMessageController!.add(message);
          break;
          
        case 'typing_status':
          _typingController!.add(data);
          break;
          
        case 'online_users':
          final users = data['users'] as List<dynamic>;
          _onlineUsersController!.add(users.cast<Map<String, dynamic>>());
          break;
          
        case 'user_joined':
        case 'user_left':
          // Handle user presence updates
          _typingController!.add(data);
          break;
      }
    });
  }

  Future<void> connect(int channelId, String token) async {
    if (_isConnected) {
      await disconnect();
    }

    try {
      final wsUrl = 'ws://localhost:8000/ws/channels/$channelId?token=$token';
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      _channel!.stream.listen(
        (data) {
          try {
            final message = json.decode(data) as Map<String, dynamic>;
            _messageController!.add(message);
          } catch (e) {
            print('Error parsing WebSocket message: $e');
          }
        },
        onError: (error) {
          print('WebSocket error: $error');
          _isConnected = false;
        },
        onDone: () {
          print('WebSocket connection closed');
          _isConnected = false;
        },
      );
      
      _isConnected = true;
      _startPingTimer();
      
    } catch (e) {
      print('Failed to connect to WebSocket: $e');
      _isConnected = false;
    }
  }

  void _startPingTimer() {
    _pingTimer?.cancel();
    _pingTimer = Timer.periodic(const Duration(seconds: 30), (timer) {
      if (_isConnected && _channel != null) {
        sendMessage({
          'type': 'ping',
          'timestamp': DateTime.now().millisecondsSinceEpoch,
        });
      }
    });
  }

  Future<void> disconnect() async {
    _pingTimer?.cancel();
    _pingTimer = null;
    
    if (_channel != null) {
      await _channel!.sink.close();
      _channel = null;
    }
    
    _isConnected = false;
  }

  void sendMessage(Map<String, dynamic> message) {
    if (_isConnected && _channel != null) {
      try {
        _channel!.sink.add(json.encode(message));
      } catch (e) {
        print('Error sending WebSocket message: $e');
      }
    }
  }

  void sendTypingStatus(bool isTyping) {
    sendMessage({
      'type': 'typing',
      'is_typing': isTyping,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    });
  }

  void markMessageAsRead(int messageId) {
    sendMessage({
      'type': 'message_read',
      'message_id': messageId,
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    });
  }

  // Getters for streams
  Stream<ChatMessage>? get newMessageStream => _newMessageStream;
  Stream<Map<String, dynamic>>? get typingStream => _typingStream;
  Stream<List<Map<String, dynamic>>>? get onlineUsersStream => _onlineUsersStream;
  
  bool get isConnected => _isConnected;

  void dispose() {
    disconnect();
    _messageController?.close();
    _newMessageController?.close();
    _typingController?.close();
    _onlineUsersController?.close();
  }
}
