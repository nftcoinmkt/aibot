import 'dart:typed_data';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_ai_bot/models/chat_message_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/utils/platform_file_uploader_stub.dart';
import 'package:image_picker_web/image_picker_web.dart';

class PlatformFileUploaderWeb implements PlatformFileUploader {
  @override
  Future<void> pickFile(
    ApiService apiService,
    int channelId,
    OnPlaceholder onPlaceholder,
    OnSuccess onSuccess,
    OnFailure onFailure,
  ) async {
    FilePickerResult? result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'doc', 'txt'],
      withData: true,
    );

    if (result != null && result.files.single.bytes != null) {
      final tempId = DateTime.now().millisecondsSinceEpoch;
      final placeholder = ChatMessage(
        id: tempId,
        channelId: channelId,
        userId: apiService.getUserId()!,
        message: 'Uploading ${result.files.single.name}...',
        timestamp: DateTime.now(),
        status: MessageStatus.sending,
      );
      onPlaceholder(placeholder);

      try {
        final message = await apiService.uploadFileInChannelWeb(
          channelId,
          result.files.single.bytes!,
          result.files.single.name,
        );
        onSuccess(message, tempId);
      } catch (e) {
        onFailure(tempId);
      }
    }
  }

  @override
  Future<void> pickImage(
    ApiService apiService,
    int channelId,
    OnPlaceholder onPlaceholder,
    OnSuccess onSuccess,
    OnFailure onFailure,
    BuildContext context, // context is not used in web but required by interface
  ) async {
    final mediaInfo = await ImagePickerWeb.getImageInfo();

    if (mediaInfo != null && mediaInfo.data != null && mediaInfo.fileName != null) {
      final tempId = DateTime.now().millisecondsSinceEpoch;
      final placeholder = ChatMessage(
        id: tempId,
        channelId: channelId,
        userId: apiService.getUserId()!,
        message: 'Uploading image...',
        timestamp: DateTime.now(),
        status: MessageStatus.sending,
      );
      onPlaceholder(placeholder);

      try {
        final message = await apiService.uploadFileInChannelWeb(
          channelId,
          mediaInfo.data!,
          mediaInfo.fileName!,
        );
        onSuccess(message, tempId);
      } catch (e) {
        onFailure(tempId);
      }
    }
  }
}

PlatformFileUploader getPlatformFileUploader() => PlatformFileUploaderWeb();
