import 'package:flutter_ai_bot/models/user_model.dart';

class ChannelMember {
  final int userId;
  final String role;
  final DateTime joinedAt;
  final User? user; // Make user optional since backend might not include user details

  ChannelMember({
    required this.userId,
    required this.role,
    required this.joinedAt,
    this.user,
  });

  factory ChannelMember.fromJson(Map<String, dynamic> json) {
    print('JSON: $json');
    return ChannelMember(
      userId: json['user_id'] ?? 0,
      role: json['role'] ?? 'member',
      joinedAt: DateTime.tryParse(json['joined_at'] ?? '') ?? DateTime.now(),
      user: json['user'] != null ? User.fromJson(json['user']) : null,
    );
  }

  @override
  String toString() {
    return 'ChannelMember{userId: $userId, role: $role, joinedAt: $joinedAt, user: $user}';
  }
}
