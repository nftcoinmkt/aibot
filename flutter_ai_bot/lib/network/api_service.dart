import 'package:http/http.dart' as http;
import 'dart:convert';
import '../models/channel_model.dart';
import '../models/user_model.dart';
import '../models/channel_member_model.dart';
import '../models/chat_message_model.dart';
import '../models/attachment_model.dart';
import 'dart:io';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'dart:typed_data';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'package:flutter/foundation.dart';

class ApiService {
  final _storage = const FlutterSecureStorage();
  static const _tokenKey = 'user_token';
  final String _baseUrl = 'http://localhost:8000/api/v1';
  final String _wsBaseUrl = 'ws://localhost:8000/api/v1';
  String? _userToken;
  int? _userId;
  WebSocketChannel? _wsChannel;

  Future<Map<String, dynamic>> signup(String email, String password, String fullName, String tenantName) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/signup'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'password': password,
        'full_name': fullName,
        'tenant_name': tenantName,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to signup: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/login/access-token'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {
        'username': email,
        'password': password,
      },
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to login: ${response.body}');
    }
  }

  Future<void> signout() async {
    _userToken = null;
    _userId = null;
    await _storage.delete(key: _tokenKey);
  }

  Future<void> forgotPassword(String email) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/forgot-password'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to send password reset email: ${response.body}');
    }
  }

  // A placeholder for the user's token. In a real app, you'd store and retrieve this securely.
  String? get userToken => _userToken;

  Future<ChatMessage> sendMessage(int channelId, String message) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/channels/$channelId/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_userToken',
      },
      body: jsonEncode({
        'message': message,
      }),
    );

    if (response.statusCode == 200) {
      return ChatMessage.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to send message: ${response.body}');
    }
  }

  Future<List<ChatMessage>> getNewMessages(int channelId, int lastMessageId) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/channels/$channelId/chat?after=$lastMessageId'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_userToken',
      },
      body: jsonEncode({}), // Sending empty body for polling
    );

    if (response.statusCode == 200) {
      final List<dynamic> messagesJson = jsonDecode(response.body);
      return messagesJson.map((json) => ChatMessage.fromJson(json)).toList();
    } else {
      throw Exception('Failed to get new messages: ${response.body}');
    }
  }

  Future<void> setToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
    _userToken = token;
    print('User token set: $_userToken');
    _userId = _getUserIdFromToken(token);
  }

  Future<bool> tryLoadToken() async {
    final token = await _storage.read(key: _tokenKey);
    if (token != null) {
      _userToken = token;
      _userId = _getUserIdFromToken(token);
      return true;
    }
    return false;
  }

  int? getUserId() => _userId;

  int? _getUserIdFromToken(String token) {
    try {
      final parts = token.split('.');
      if (parts.length != 3) return null;
      final payload = json.decode(
        utf8.decode(base64Url.decode(base64Url.normalize(parts[1]))),
      );
      final sub = payload['sub'];
      print('User ID from token: $sub');
      if (sub is int) return sub;
      if (sub is String) return int.tryParse(sub);
      return null;
    } catch (e) {
      print('Error decoding token: $e');
      return null;
    }
  }

  Future<List<Channel>> getChannels() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/channels'),
      headers: {'Authorization': 'Bearer $_userToken'},
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      return body.map((dynamic item) => Channel.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load channels');
    }
  }

  Future<Channel> createChannel(String name, String description) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/channels'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_userToken',
      },
      body: jsonEncode({'name': name, 'description': description}),
    );

    if (response.statusCode == 200) {
      return Channel.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to create channel');
    }
  }

  Future<void> addMemberToChannel(int channelId, int userId) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/channels/$channelId/members'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_userToken',
      },
      body: jsonEncode({'user_id': userId, 'role': 'member'}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to add member');
    }
  }

  Future<void> removeMemberFromChannel(int channelId, int userId) async {
    final response = await http.delete(
      Uri.parse('$_baseUrl/channels/$channelId/members/$userId'),
      headers: {'Authorization': 'Bearer $_userToken'},
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to remove member');
    }
  }

  Future<List<User>> getUsers() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/users/list'),
      headers: {'Authorization': 'Bearer $_userToken'},
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      return body.map((dynamic item) => User.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load users');
    }
  }

  Future<List<ChannelMember>> getChannelMembers(int channelId) async {
    final response = await http.get(
      Uri.parse('$_baseUrl/channels/$channelId/members'),
      headers: {'Authorization': 'Bearer $_userToken'},
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      print('Body: $body');
      return body.where((item) => item != null).map((dynamic item) {
        try {
          print('Item: $item');
          return ChannelMember.fromJson(item as Map<String, dynamic>);
        } catch (e) {
          print('Error parsing channel member: $e');
          print('Item: $item');
          // Return a fallback member
          return ChannelMember(
            userId: item['user_id'] ?? 0,
            role: item['role'] ?? 'member',
            joinedAt: DateTime.now(),
          );
        }
      }).toList();
    } else {
      throw Exception('Failed to load channel members');
    }
  }

  Future<ChatMessage> sendMessageInChannel(int channelId, String message) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/channels/$channelId/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_userToken',
      },
      body: jsonEncode({'message': message}),
    );

    if (response.statusCode == 200) {
      return ChatMessage.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to send message');
    }
  }

  Future<List<ChatMessage>> getChannelMessages(int channelId) async {
    // NOTE: The endpoint for getting channel messages is not in the Postman collection.
    // This is a placeholder implementation assuming the endpoint is /channels/{id}/messages
    final response = await http.get(
      Uri.parse('$_baseUrl/channels/$channelId/messages'),
      headers: {'Authorization': 'Bearer $_userToken'},
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      return body.map((dynamic item) => ChatMessage.fromJson(item)).toList();
    } else {
      // Returning empty list for now as the endpoint is not available
      print('Failed to load messages: ${response.body}');
      return [];
      // throw Exception('Failed to load messages');
    }
  }

  // Placeholder for file upload for web. The API does not currently support this.
  Future<ChatMessage> uploadFileInChannelWeb(int channelId, Uint8List fileBytes, String fileName) async {
    // Create a multipart request
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/channels/$channelId/upload'), // Assuming this endpoint
    );
    request.headers['Authorization'] = 'Bearer $_userToken';
    request.files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: fileName));

    // In a real implementation, you would send the request and handle the response.
    // For now, we'll simulate a response.
    print('Simulating web file upload for: $fileName');
    await Future.delayed(const Duration(seconds: 2)); // Simulate network delay

    // This is a mock response. The actual API would return something different.
    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch,
      channelId: channelId,
      userId: _userId!,
      message: 'File: $fileName', // Placeholder message
      timestamp: DateTime.now(),
      attachment: Attachment(id: '1', fileUrl: '', fileName: fileName, fileType: 'file'),
    );
  }

  // Placeholder for file upload. The API does not currently support this.
  Future<ChatMessage> uploadFileInChannel(int channelId, File file) async {
    // Create a multipart request
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/channels/$channelId/upload'), // Assuming this endpoint
    );
    request.headers['Authorization'] = 'Bearer $_userToken';
    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    // In a real implementation, you would send the request and handle the response.
    // For now, we'll simulate a response.
    print('Simulating file upload for: ${file.path}');
    await Future.delayed(Duration(seconds: 2)); // Simulate network delay

    // This is a mock response. The actual API would return something different.
    return ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch,
      channelId: channelId,
      userId: _userId!,
      message: 'File: ${file.path.split('/').last}', // Placeholder message
      timestamp: DateTime.now(),
    );
  }

  // WebSocket methods for real-time chat
  WebSocketChannel connectToChannelChat(int channelId) {
    try {
      _wsChannel = WebSocketChannel.connect(
        Uri.parse('$_wsBaseUrl/channels/$channelId/stream?token=$_userToken'),
      );
      return _wsChannel!;
    } catch (e) {
      print('Failed to connect WebSocket: $e');
      rethrow;
    }
  }

  WebSocketChannel connectToGeneralChat() {
    try {
      _wsChannel = WebSocketChannel.connect(
        Uri.parse('$_wsBaseUrl/chat/stream?token=$_userToken'),
      );
      return _wsChannel!;
    } catch (e) {
      print('Failed to connect WebSocket: $e');
      rethrow;
    }
  }

  void sendWebSocketMessage(String message, {int? channelId}) {
    if (_wsChannel != null) {
      final payload = {
        'message': message,
        if (channelId != null) 'channel_id': channelId,
      };
      _wsChannel!.sink.add(jsonEncode(payload));
    }
  }

  void closeWebSocket() {
    _wsChannel?.sink.close();
    _wsChannel = null;
  }
}
