import 'package:flutter/material.dart';
import 'package:flutter_ai_bot/models/chat_message_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';

typedef OnPlaceholder = void Function(ChatMessage placeholder);
typedef OnSuccess = void Function(ChatMessage finalMessage, int tempId);
typedef OnFailure = void Function(int tempId);

abstract class PlatformFileUploader {
  Future<void> pickFile(
    ApiService apiService,
    int channelId,
    OnPlaceholder onPlaceholder,
    OnSuccess onSuccess,
    OnFailure onFailure,
  );

  Future<void> pickImage(
    ApiService apiService,
    int channelId,
    OnPlaceholder onPlaceholder,
    OnSuccess onSuccess,
    OnFailure onFailure,
    BuildContext context,
  );
}
