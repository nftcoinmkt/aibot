import 'package:flutter_ai_bot/models/attachment_model.dart';

enum MessageStatus { sent, sending, failed }

class ChatMessage {
  final int id;
  final int channelId;
  final int userId;
  final String message;
  final Attachment? attachment;
  final MessageStatus status;
  final DateTime timestamp;

  ChatMessage({
    required this.id,
    required this.channelId,
    required this.userId,
    required this.message,
    this.attachment,
    this.status = MessageStatus.sent,
    required this.timestamp,
  });

  ChatMessage copyWith({
    int? id,
    MessageStatus? status,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      channelId: this.channelId,
      userId: this.userId,
      message: this.message,
      attachment: this.attachment,
      status: status ?? this.status,
      timestamp: this.timestamp,
    );
  }

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: json['id'] ?? 0,
      channelId: json['channelId'] ?? json['channel_id'] ?? 0,
      userId: json['userId'] ?? json['user_id'] ?? -1, // Use -1 for AI messages
      message: json['message'] ?? json['response'] ?? '',
      attachment: json['attachment'] != null ? Attachment.fromJson(json['attachment']) : null,
      status: MessageStatus.sent, // Default status for incoming messages
      timestamp: DateTime.tryParse(json['timestamp'] ?? json['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}
