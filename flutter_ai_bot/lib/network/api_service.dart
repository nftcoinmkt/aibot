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
import 'package:flutter/foundation.dart';

class ApiService {
  final _storage = const FlutterSecureStorage();
  static const _tokenKey = 'user_token';
  late final String _baseUrl;
  String? _userToken;
  int? _userId;

  ApiService() {
    // Environment-based URL configuration
    if (kDebugMode) {
      // Local development
      _baseUrl = 'http://localhost:8000/api/v1';
    } else {
      // Production/Cloud deployment
      _baseUrl = 'https://aibot-backend-272236378462.us-central1.run.app/api/v1';
    }
  }

  // Returns the origin/base host without the API prefix, e.g. http://localhost:8000
  String get baseOrigin {
    // Remove trailing /api/v1 (or variant with/without trailing slash)
    return _baseUrl.replaceFirst(RegExp(r"/api/v1$"), "");
  }

  // Resolve a file path (e.g. /uploads/...) to a full URL
  String resolveFileUrl(String filePath) {
    if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
      return filePath;
    }
    final normalized = filePath.startsWith('/') ? filePath : '/$filePath';
    return '$baseOrigin$normalized';
  }

  Future<List<Map<String, dynamic>>> getAvailableTenants() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/tenants'),
      headers: {'Content-Type': 'application/json'},
    );

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return List<Map<String, dynamic>>.from(data['tenants']);
    } else {
      throw Exception('Failed to load tenants: ${response.body}');
    }
  }

  Future<Map<String, dynamic>> signup(
    String email,
    String password,
    String fullName,
    String tenantName
  ) async {
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

    if (response.statusCode == 201) {
      return jsonDecode(response.body);
    } else {
      String errorMessage = 'Failed to signup';
      try {
        final errorData = jsonDecode(response.body);
        if (errorData['detail'] != null) {
          errorMessage = errorData['detail'];
        }
      } catch (e) {
        errorMessage = 'Failed to signup: ${response.body}';
      }
      throw Exception(errorMessage);
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
      String errorMessage = 'Failed to login';
      try {
        final errorData = jsonDecode(response.body);
        if (errorData['detail'] != null) {
          errorMessage = errorData['detail'];
        }
      } catch (e) {
        if (response.statusCode == 400) {
          errorMessage = 'Invalid email or password';
        } else {
          errorMessage = 'Login failed: ${response.body}';
        }
      }
      throw Exception(errorMessage);
    }
  }

  Future<void> signout() async {
    _userToken = null;
    _userId = null;
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: 'user_id');
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

  Future<void> setToken(String token, {int? userId}) async {
    print('💾 Storing token: ${token.substring(0, 20)}... with key: $_tokenKey');
    await _storage.write(key: _tokenKey, value: token);
    _userToken = token;
    if (userId != null) {
      _userId = userId;
      await _storage.write(key: 'user_id', value: userId.toString());
      print('👤 Stored user ID: $userId');
    }
    print('✅ Token and user data stored successfully');
  }

  Future<bool> tryLoadToken() async {
    final token = await _storage.read(key: _tokenKey);
    final userIdStr = await _storage.read(key: 'user_id');
    if (token != null) {
      _userToken = token;
      _userId = userIdStr != null ? int.tryParse(userIdStr) : null;
      return true;
    }
    return false;
  }

  int? getUserId() => _userId;

  Future<String?> getToken() async {
    final token = await _storage.read(key: _tokenKey);
    print('🔑 Token retrieval: ${token != null ? "Found token (${token.substring(0, 20)}...)" : "No token found"}');
    return token;
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

  Future<List<ChatMessage>> sendMessageInChannel(int channelId, String message) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/channels/$channelId/chat'),
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer $_userToken',
      },
      body: jsonEncode({'message': message}),
    );

    if (response.statusCode == 200) {
      final responseData = jsonDecode(response.body);
      final List<dynamic> messagesJson = responseData['messages'];
      return messagesJson.map((json) => ChatMessage.fromJson(json)).toList();
    } else {
      throw Exception('Failed to send message: ${response.body}');
    }
  }

  Future<List<ChatMessage>> getChannelMessages(int channelId, {int daysBack = 2}) async {
    final response = await http.get(
      Uri.parse('$_baseUrl/channels/$channelId/messages?days_back=$daysBack'),
      headers: {'Authorization': 'Bearer $_userToken'},
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      return body.map((dynamic item) => ChatMessage.fromJson(item)).toList();
    } else {
      print('Failed to load messages: ${response.body}');
      throw Exception('Failed to load messages: ${response.body}');
    }
  }

  Future<List<ChatMessage>> getAllChannelMessages(int channelId) async {
    final response = await http.get(
      Uri.parse('$_baseUrl/channels/$channelId/messages/all'),
      headers: {'Authorization': 'Bearer $_userToken'},
    );

    if (response.statusCode == 200) {
      List<dynamic> body = jsonDecode(response.body);
      return body.map((dynamic item) => ChatMessage.fromJson(item)).toList();
    } else {
      print('Failed to load all messages: ${response.body}');
      throw Exception('Failed to load all messages: ${response.body}');
    }
  }

  Future<List<ChatMessage>> uploadFileInChannelWeb(int channelId, Uint8List fileBytes, String fileName) async {
    // Create a multipart request
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/channels/$channelId/upload'),
    );
    request.headers['Authorization'] = 'Bearer $_userToken';
    request.files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: fileName));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final responseData = jsonDecode(response.body);
      final List<dynamic> messagesJson = responseData['messages'];
      return messagesJson.map((json) => ChatMessage.fromJson(json)).toList();
    } else {
      throw Exception('Failed to upload file: ${response.body}');
    }
  }

  Future<List<ChatMessage>> uploadFileInChannel(int channelId, File file) async {
    // Create a multipart request
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('$_baseUrl/channels/$channelId/upload'),
    );
    request.headers['Authorization'] = 'Bearer $_userToken';
    request.files.add(await http.MultipartFile.fromPath('file', file.path));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode == 200) {
      final responseData = jsonDecode(response.body);
      final List<dynamic> messagesJson = responseData['messages'];
      return messagesJson.map((json) => ChatMessage.fromJson(json)).toList();
    } else {
      throw Exception('Failed to upload file: ${response.body}');
    }
  }


}
