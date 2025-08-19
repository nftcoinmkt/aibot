import 'package:flutter_ai_bot/models/user_model.dart';

class ChannelMember {
  final int userId;
  final String role;
  final DateTime joinedAt;
  final User? user; // Make user optional since backend might not include user details
  final String? userFullName; // Direct user name from backend
  final String? userEmail; // Direct user email from backend

  ChannelMember({
    required this.userId,
    required this.role,
    required this.joinedAt,
    this.user,
    this.userFullName,
    this.userEmail,
  });

  factory ChannelMember.fromJson(Map<String, dynamic> json) {
    print('ChannelMember JSON: $json');
    return ChannelMember(
      userId: json['user_id'] ?? 0,
      role: json['role'] ?? 'member',
      joinedAt: DateTime.tryParse(json['joined_at'] ?? '') ?? DateTime.now(),
      user: json['user'] != null ? User.fromJson(json['user']) : null,
      userFullName: json['user_full_name'],
      userEmail: json['user_email'],
    );
  }

  @override
  String toString() {
    return 'ChannelMember{userId: $userId, role: $role, joinedAt: $joinedAt, user: $user}';
  }
}
