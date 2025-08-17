import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_ai_bot/models/chat_message_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/utils/platform_file_uploader_stub.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as p;

class PlatformFileUploaderIO implements PlatformFileUploader {
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
    );

    if (result != null && result.files.single.path != null) {
      File file = File(result.files.single.path!);
      final tempId = DateTime.now().millisecondsSinceEpoch;
      final placeholder = ChatMessage(
        id: tempId,
        channelId: channelId,
        userId: apiService.getUserId()!,
        message: 'Uploading ${p.basename(file.path)}...',
        timestamp: DateTime.now(),
        status: MessageStatus.sending,
      );
      onPlaceholder(placeholder);

      try {
        final messages = await apiService.uploadFileInChannel(channelId, file);
        // For file upload, we expect user message + AI analysis
        for (final message in messages) {
          onSuccess(message, tempId);
        }
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
    BuildContext context,
  ) async {
    final source = await _showImageSourceDialog(context);
    if (source == null) return;

    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: source);

    if (pickedFile != null) {
      File imageFile = File(pickedFile.path);
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
        final messages = await apiService.uploadFileInChannel(channelId, imageFile);
        // For image upload, we expect user message + AI analysis
        for (final message in messages) {
          onSuccess(message, tempId);
        }
      } catch (e) {
        onFailure(tempId);
      }
    }
  }

  Future<ImageSource?> _showImageSourceDialog(BuildContext context) async {
    return showDialog<ImageSource>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Select Image Source'),
        content: Text('Choose where to pick the image from.'),
        actions: [
          TextButton(
            child: Text('Camera'),
            onPressed: () => Navigator.pop(context, ImageSource.camera),
          ),
          TextButton(
            child: Text('Gallery'),
            onPressed: () => Navigator.pop(context, ImageSource.gallery),
          ),
        ],
      ),
    );
  }
}

PlatformFileUploader getPlatformFileUploader() => PlatformFileUploaderIO();
