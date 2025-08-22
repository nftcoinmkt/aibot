import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_ai_bot/models/attachment_model.dart';
import 'package:flutter_ai_bot/models/channel_model.dart';
import 'package:flutter_ai_bot/models/channel_member_model.dart';
import 'package:flutter_ai_bot/models/chat_message_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'dart:async';
import 'package:flutter_ai_bot/utils/platform_file_uploader.dart';
import 'package:flutter_ai_bot/views/channel_details_view.dart';
import 'package:flutter_ai_bot/widgets/file_preview_dialog.dart';
import 'package:flutter_ai_bot/widgets/file_upload_dialog.dart';
import 'package:flutter_ai_bot/services/websocket_service.dart';
import 'package:image_picker/image_picker.dart';
import 'package:file_picker/file_picker.dart';
import 'package:cross_file/cross_file.dart';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'dart:async';
import 'package:path/path.dart' as path;


class ChatView extends StatefulWidget {
  final Channel channel;
  final ApiService apiService;

  const ChatView({super.key, required this.channel, required this.apiService});

  @override
  _ChatViewState createState() => _ChatViewState();
}

class _ChatViewState extends State<ChatView> {
  final TextEditingController _controller = TextEditingController();
  List<ChatMessage> _messages = [];
  int? _currentUserId;

  bool _isLoading = true;
  bool _showingAllMessages = false;
  final PlatformFileUploader _fileUploader = getPlatformFileUploader();
  int _lastMessageId = 0;

  // File attachment state
  dynamic _selectedFile;
  String _selectedFileName = '';
  String _selectedFileType = '';

  // WebSocket for real-time updates
  WebSocketService? _webSocketService;
  StreamSubscription<ChatMessage>? _newMessageSubscription;

  StreamSubscription<List<Map<String, dynamic>>>? _onlineUsersSubscription;

  // Real-time state
  List<Map<String, dynamic>> _onlineUsers = [];

  // User mapping for displaying names
  Map<int, String> _userNames = {};

  @override
  void initState() {
    super.initState();
    _currentUserId = widget.apiService.getUserId();
    _loadMessages();
    _loadChannelMembers();
    _initializeWebSocket();



    // Update UI every 5 seconds to reflect WebSocket connection status
    Timer.periodic(const Duration(seconds: 5), (timer) {
      if (mounted) {
        setState(() {
          // This will trigger a rebuild to update the connection status indicator
        });
      } else {
        timer.cancel();
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    _webSocketService?.dispose();
    _newMessageSubscription?.cancel();
    _onlineUsersSubscription?.cancel();
    super.dispose();
  }

  Future<void> _initializeWebSocket() async {
    try {
      print('🚀 Initializing WebSocket for channel: ${widget.channel.id}');
      _webSocketService = WebSocketService();
      final token = await widget.apiService.getToken();

      print('🔑 Retrieved token: ${token != null ? "✅ Available" : "❌ Missing"}');
      if (token != null) {
        print('🔌 Connecting to WebSocket...');
        await _webSocketService!.connect(widget.channel.id, token);

        // Listen for new messages
        print('👂 Setting up WebSocket message listener...');
        _newMessageSubscription = _webSocketService!.newMessageStream?.listen((message) {
          print('📨 Received new message via WebSocket: ${message.id}');
          if (mounted) {
            setState(() {
              // Only add if not already in the list (avoid duplicates)
              // Check both by ID and by content/timestamp for better deduplication
              final exists = _messages.any((m) =>
                m.id == message.id ||
                (m.message == message.message &&
                 m.userId == message.userId &&
                 m.timestamp.difference(message.timestamp).abs().inSeconds < 2)
              );

              if (!exists) {
                print('✅ Adding new WebSocket message: ${message.id} - ${message.message.substring(0, message.message.length > 50 ? 50 : message.message.length)}...');
                // Insert at the correct position to maintain chronological order
                _insertMessageInOrder(message);
                if (message.id > _lastMessageId) {
                  _lastMessageId = message.id;
                }
              } else {
                print('⚠️ Duplicate message detected, skipping: ${message.id}');
              }
            });
          }
        });



        // Listen for online users
        _onlineUsersSubscription = _webSocketService!.onlineUsersStream?.listen((users) {
          if (mounted) {
            print('👥 Received online users update: ${users.length} users');
            setState(() {
              _onlineUsers = users;
            });
          }
        });
      }
    } catch (e) {
      print('❌ Failed to initialize WebSocket: $e');
      // Show error to user
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to connect to real-time chat: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }





  void _insertMessageInOrder(ChatMessage message) {
    // Find the correct position to insert the message based on timestamp
    // Since ListView is reversed, newer messages (later timestamps) go at lower indices
    int insertIndex = 0;

    // If list is empty, just add at index 0
    if (_messages.isEmpty) {
      _messages.insert(0, message);
      return;
    }

    // Find the correct position
    for (int i = 0; i < _messages.length; i++) {
      if (message.timestamp.isAfter(_messages[i].timestamp)) {
        insertIndex = i;
        break;
      }
      insertIndex = i + 1;
    }

    // Ensure we don't exceed list bounds
    if (insertIndex > _messages.length) {
      insertIndex = _messages.length;
    }

    _messages.insert(insertIndex, message);
    print('Inserted message at index $insertIndex of ${_messages.length} total messages');
  }

  void _loadMessages() async {
    try {
      final historicalMessages = await widget.apiService.getChannelMessages(widget.channel.id);
      if (mounted) {
        setState(() {
          // Backend returns messages in chronological order (oldest first)
          // Reverse for ListView (newest first at index 0)
          _messages = historicalMessages.reversed.toList();
          if (_messages.isNotEmpty) {
            _lastMessageId = _messages.first.id;
          }
          _isLoading = false;
          _showingAllMessages = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load messages: $e')),
        );
      }
    }
  }

  void _loadAllMessages() async {
    try {
      final allMessages = await widget.apiService.getAllChannelMessages(widget.channel.id);
      if (mounted) {
        setState(() {
          // Backend returns messages in chronological order (oldest first)
          // Reverse for ListView (newest first at index 0)
          _messages = allMessages.reversed.toList();
          if (_messages.isNotEmpty) {
            _lastMessageId = _messages.first.id;
          }
          _showingAllMessages = true;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to load all messages: $e')),
        );
      }
    }
  }

  void _loadChannelMembers() async {
    try {
      final members = await widget.apiService.getChannelMembers(widget.channel.id);
      if (mounted) {
        setState(() {
          // Create mapping of user ID to full name
          _userNames = {
            for (var member in members)
              member.userId: _getUserDisplayName(member)
          };
          print('📋 Loaded ${_userNames.length} channel members: $_userNames');
        });
      }
    } catch (e) {
      print('❌ Failed to load channel members: $e');
      // Don't show error to user as this is not critical
    }
  }

  String _getUserDisplayName(ChannelMember member) {
    // Try different sources for user name in order of preference
    if (member.userFullName != null && member.userFullName!.isNotEmpty) {
      return member.userFullName!;
    } else if (member.user?.fullName != null && member.user!.fullName.isNotEmpty) {
      return member.user!.fullName;
    } else if (member.userEmail != null && member.userEmail!.isNotEmpty) {
      return member.userEmail!;
    } else if (member.user?.email != null && member.user!.email.isNotEmpty) {
      return member.user!.email;
    } else {
      return 'User ${member.userId}';
    }
  }

  void _sendMessage() async {
    final text = _controller.text.trim();

    // Check if we have a file to upload
    if (_selectedFile != null) {
      await _sendMessageWithFile(text);
      return;
    }

    // Regular text message
    if (text.isEmpty) return;
    if (_currentUserId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('User not authenticated')),
      );
      return;
    }

    final messageText = _controller.text;
    _controller.clear();

    // Create a temporary message to show immediately
    final tempMessage = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch,
      channelId: widget.channel.id,
      userId: _currentUserId!,
      message: messageText,
      timestamp: DateTime.now(),
      status: MessageStatus.sending,
    );

    // Add message to UI immediately
    setState(() {
      _insertMessageInOrder(tempMessage);
    });

    try {
      // Send message via API to ensure it's saved
      print('Sending message to API: $messageText');
      final messages = await widget.apiService.sendMessageInChannel(widget.channel.id, messageText);
      print('Received ${messages.length} messages from API');

      // Remove the temporary message and add the real messages (user + AI response)
      setState(() {
        final index = _messages.indexWhere((m) => m.id == tempMessage.id);
        if (index != -1) {
          _messages.removeAt(index);
          print('Removed temporary message at index $index');
        }

        // Add the messages in chronological order
        // Sort the received messages by timestamp to ensure proper order
        final sortedMessages = messages.toList()
          ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

        for (final message in sortedMessages) {
          print('Adding API message: ${message.id} - ${message.message.substring(0, message.message.length > 50 ? 50 : message.message.length)}...');
          _insertMessageInOrder(message.copyWith(status: MessageStatus.sent));
          if (message.id > _lastMessageId) {
            _lastMessageId = message.id;
          }
        }
      });

    } catch (e) {
      // Mark message as failed
      setState(() {
        final index = _messages.indexWhere((m) => m.id == tempMessage.id);
        if (index != -1) {
          _messages[index] = tempMessage.copyWith(status: MessageStatus.failed);
        }
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to send message: $e')),
      );
    }
  }

  Future<void> _sendMessageWithFile(String text) async {
    if (_selectedFile == null) return;

    final messageText = text.isNotEmpty ? text : '';

    _controller.clear();

    // Create placeholder message
    final tempId = DateTime.now().millisecondsSinceEpoch;
    final placeholderText = messageText.isNotEmpty
        ? '$messageText\n\n📎 Uploading $_selectedFileName...'
        : '📎 Uploading $_selectedFileName...';

    final placeholder = ChatMessage(
      id: tempId,
      channelId: widget.channel.id,
      userId: _currentUserId!,
      message: placeholderText,
      timestamp: DateTime.now(),
      status: MessageStatus.sending,
    );

    setState(() {
      _insertMessageInOrder(placeholder);
    });

    try {
      List<ChatMessage> messages;

      if (kIsWeb) {
        // Web platform
        Uint8List bytes;
        if (_selectedFile is Uint8List) {
          // File picker result
          bytes = _selectedFile as Uint8List;
        } else if (_selectedFile is XFile) {
          // Image picker result
          bytes = await (_selectedFile as XFile).readAsBytes();
        } else {
          throw Exception('Unsupported file type for web');
        }

        messages = await widget.apiService.uploadFileInChannelWeb(
          widget.channel.id,
          bytes,
          _selectedFileName
        );
      } else {
        // Mobile platforms
        File file;
        if (_selectedFile is File) {
          file = _selectedFile as File;
        } else {
          throw Exception('Expected File object for mobile platform');
        }

        messages = await widget.apiService.uploadFileInChannel(widget.channel.id, file);
      }

      // If user provided text, update the user message to include it
      if (messageText.isNotEmpty && messages.isNotEmpty) {
        final userMessage = messages.first;
        final updatedUserMessage = ChatMessage(
          id: userMessage.id,
          channelId: userMessage.channelId,
          userId: userMessage.userId,
          message: '$messageText\n\n${userMessage.message}',
          attachment: userMessage.attachment,
          status: userMessage.status,
          timestamp: userMessage.timestamp,
        );
        messages[0] = updatedUserMessage;
      }

      setState(() {
        // Remove placeholder
        _messages.removeWhere((m) => m.id == tempId);

        // Add all messages (user + AI response) in chronological order
        final sortedMessages = messages.toList()
          ..sort((a, b) => a.timestamp.compareTo(b.timestamp));

        for (final message in sortedMessages) {
          _insertMessageInOrder(message.copyWith(status: MessageStatus.sent));
          if (message.id > _lastMessageId) {
            _lastMessageId = message.id;
          }
        }

        // Clear selected file
        _selectedFile = null;
        _selectedFileName = '';
        _selectedFileType = '';
      });

    } catch (e) {
      // Mark as failed
      setState(() {
        final index = _messages.indexWhere((m) => m.id == tempId);
        if (index != -1) {
          final failedMessage = ChatMessage(
            id: placeholder.id,
            channelId: placeholder.channelId,
            userId: placeholder.userId,
            message: messageText.isNotEmpty
                ? '$messageText\n\n❌ Failed to upload $_selectedFileName'
                : '❌ Failed to upload $_selectedFileName',
            attachment: placeholder.attachment,
            status: MessageStatus.failed,
            timestamp: placeholder.timestamp,
          );
          _messages[index] = failedMessage;
        }
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to upload file: $e')),
        );
      }
    }
  }

  void _pickFile() async {
    if (!mounted) return;

    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'doc', 'docx', 'txt'],
      );

      if (result != null) {
        setState(() {
          // Handle platform differences
          if (kIsWeb) {
            // Web platform
            if (result.files.single.bytes != null) {
              _selectedFile = result.files.single.bytes!;
            } else {
              throw Exception('File bytes are null on web platform');
            }
          } else {
            // Mobile platforms (Android/iOS)
            if (result.files.single.path != null) {
              _selectedFile = File(result.files.single.path!);
            } else {
              throw Exception('File path is null on mobile platform');
            }
          }
          _selectedFileName = result.files.single.name;
          _selectedFileType = 'file';
        });
      }
    } catch (e) {
      if (!mounted) return;
      print('File picker error: $e'); // Debug log
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to pick file: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }


  void _pickImage() async {
    if (!mounted) return;

    try {
      final ImagePicker picker = ImagePicker();

      ImageSource? source;

      if (kIsWeb) {
        // On web, only gallery is available
        source = ImageSource.gallery;
      } else {
        // Show image source selection for mobile
        source = await showDialog<ImageSource>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('Select Image Source'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  leading: const Icon(CupertinoIcons.camera),
                  title: const Text('Camera'),
                  onTap: () => Navigator.pop(context, ImageSource.camera),
                ),
                ListTile(
                  leading: const Icon(CupertinoIcons.photo),
                  title: const Text('Gallery'),
                  onTap: () => Navigator.pop(context, ImageSource.gallery),
                ),
              ],
            ),
          ),
        );
      }

      if (source != null) {
        final XFile? image = await picker.pickImage(source: source);
        if (image != null) {
          setState(() {
            if (kIsWeb) {
              // For web, we'll need to read bytes
              _selectedFile = image; // Store XFile for web
            } else {
              // For mobile, use File
              _selectedFile = File(image.path);
            }
            _selectedFileName = image.name;
            _selectedFileType = 'image';
          });
        }
      }
    } catch (e) {
      if (!mounted) return;
      print('Image picker error: $e'); // Debug log
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to pick image: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _clearSelectedFile() {
    setState(() {
      _selectedFile = null;
      _selectedFileName = '';
      _selectedFileType = '';
    });
  }




  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF25D366),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(CupertinoIcons.back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        titleSpacing: 0,
        title: InkWell(
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => ChannelDetailsView(
                  channel: widget.channel,
                  apiService: widget.apiService,
                ),
              ),
            );
          },
          child: Row(
            children: [
              Container(
                width: 35,
                height: 35,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(17.5),
                ),
                child: Center(
                  child: Text(
                    widget.channel.name.isNotEmpty ? widget.channel.name[0].toUpperCase() : '#',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      widget.channel.name,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                    Row(
                      children: [
                        Container(
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: _webSocketService?.isConnected == true ? Colors.green : Colors.red,
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          _webSocketService?.isConnected == true ? 'Connected' : 'Disconnected',
                          style: TextStyle(
                            color: Colors.white.withOpacity(0.8),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
          // WebSocket reconnect button
          IconButton(
            icon: Icon(
              _webSocketService?.isConnected == true ? CupertinoIcons.wifi : CupertinoIcons.wifi_slash,
              color: _webSocketService?.isConnected == true ? Colors.white : Colors.red,
            ),
            onPressed: () async {
              print('🔄 Manual WebSocket reconnection requested');
              await _initializeWebSocket();
            },
          ),
          IconButton(
            icon: const Icon(CupertinoIcons.info_circle, color: Colors.white),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => ChannelDetailsView(
                    channel: widget.channel,
                    apiService: widget.apiService,
                  ),
                ),
              );
            },
          ),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(
          color: Color(0xFFE5DDD5),
        ),
        child: SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.max,
            children: [
              Expanded(
                child: _isLoading
                    ? const Center(child: CircularProgressIndicator())
                    : Column(
                        children: [
                          if (!_showingAllMessages && _messages.isNotEmpty)
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.all(8),
                              child: ElevatedButton.icon(
                                onPressed: _loadAllMessages,
                                icon: const Icon(CupertinoIcons.clock, size: 16),
                                label: const Text('Load Older Messages'),
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF075E54),
                                  foregroundColor: Colors.white,
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(20),
                                  ),
                                ),
                              ),
                            ),
                          Expanded(
                            child: Column(
                              children: [
                                // Online users indicator
                                if (_onlineUsers.isNotEmpty)
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                                    child: Row(
                                      children: [
                                        Icon(
                                          CupertinoIcons.circle_fill,
                                          color: Colors.green,
                                          size: 8,
                                        ),
                                        const SizedBox(width: 8),
                                        Text(
                                          '${_onlineUsers.length} online',
                                          style: TextStyle(
                                            color: Colors.grey[600],
                                            fontSize: 12,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),

                                Expanded(
                                  child: ListView.builder(
                                    reverse: true,
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                    itemCount: _messages.length,
                                    itemBuilder: (context, index) {
                                      final message = _messages[index];
                                      final isMe = message.userId == _currentUserId;
                                      final isAI = message.userId == -1; // AI messages have userId -1
                                      return _buildMessageBubble(message, isMe, isAI: isAI);
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
              ),
              Container(
                color: Colors.white,
                child: SafeArea(
                  top: false,
                  child: _buildMessageComposer(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }


  Widget _buildMessageBubble(ChatMessage message, bool isMe, {bool isAI = false}) {
    return Container(
      margin: const EdgeInsets.symmetric(vertical: 2, horizontal: 8),
      child: Row(
        mainAxisAlignment: isMe ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          if (!isMe) 
            Container(
              width: 30,
              height: 30,
              margin: const EdgeInsets.only(right: 8, bottom: 4),
              decoration: BoxDecoration(
                color: isAI ? Colors.blue.withOpacity(0.1) : const Color(0xFF25D366).withOpacity(0.1),
                borderRadius: BorderRadius.circular(15),
              ),
              child: Center(
                child: Icon(
                  isAI ? CupertinoIcons.sparkles : CupertinoIcons.person,
                  size: 16,
                  color: isAI ? Colors.blue : const Color(0xFF25D366),
                ),
              ),
            ),
          Flexible(
            child: ConstrainedBox(
              constraints: BoxConstraints(
                maxWidth: MediaQuery.of(context).size.width * 0.75,
              ),
              child: _buildMessageContent(message, isMe, isAI: isAI),
            ),
          ),
          if (isMe) ...[
            const SizedBox(width: 4),
            _buildMessageStatus(message),
          ],
        ],
      ),
    );
  }

  Widget _buildMessageStatus(ChatMessage message) {
    switch (message.status) {
      case MessageStatus.sending:
        return Container(
          margin: const EdgeInsets.only(bottom: 4),
          child: const Icon(CupertinoIcons.clock, size: 12, color: Colors.grey),
        );
      case MessageStatus.failed:
        return Container(
          margin: const EdgeInsets.only(bottom: 4),
          child: const Icon(CupertinoIcons.exclamationmark_circle, size: 12, color: Colors.red),
        );
      case MessageStatus.sent:
        return Container(
          margin: const EdgeInsets.only(bottom: 4),
          child: const Icon(CupertinoIcons.checkmark, size: 12, color: Colors.grey),
        );
    }
  }

  String _getSenderName(ChatMessage message, bool isMe, bool isAI) {
    if (isAI) {
      return 'AI Bot';
    } else if (isMe) {
      return 'You';
    } else {
      // Use the user mapping to get the actual user name
      final userName = _userNames[message.userId];
      if (userName != null) {
        return userName;
      } else {
        // User not found in channel members (possibly deleted)
        return 'Unknown User';
      }
    }
  }

  Widget _buildMessageContent(ChatMessage message, bool isMe, {bool isAI = false}) {
    final bubbleColor = isMe
        ? const Color(0xFFDCF8C6)
        : isAI
            ? const Color(0xFFE3F2FD)
            : Colors.white;
    final bubbleRadius = BorderRadius.only(
      topLeft: const Radius.circular(18),
      topRight: const Radius.circular(18),
      bottomLeft: isMe ? const Radius.circular(18) : const Radius.circular(4),
      bottomRight: isMe ? const Radius.circular(4) : const Radius.circular(18),
    );

    return Container(
      constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.75),
      margin: const EdgeInsets.symmetric(vertical: 2),
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
      decoration: BoxDecoration(
        color: bubbleColor,
        borderRadius: bubbleRadius,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 2,
            offset: const Offset(0, 1),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Sender name - show for all messages
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Text(
              _getSenderName(message, isMe, isAI),
              style: TextStyle(
                color: isAI
                    ? Colors.blue[700]
                    : isMe
                        ? Colors.green[700]
                        : const Color(0xFF25D366),
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
          if (message.attachment != null)
            _buildAttachmentView(message.attachment!),
          Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Flexible(
                child: Text(
                  message.message,
                  style: const TextStyle(
                    color: Colors.black87,
                    fontSize: 16,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Tooltip(
                message: _formatFullTimestamp(message.timestamp),
                child: Text(
                  _formatTime(message.timestamp),
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 11,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAttachmentView(Attachment attachment) {
    final fileExtension = path.extension(attachment.fileName).toLowerCase();
    final isImage = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'].contains(fileExtension);
    final isPdf = fileExtension == '.pdf';

    return GestureDetector(
      onTap: () => _showFilePreview(attachment),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.grey.withOpacity(0.3)),
        ),
        child: isImage
            ? _buildImageThumbnail(attachment)
            : _buildFileAttachment(attachment, fileExtension, isImage, isPdf),
      ),
    );
  }

  Widget _buildImageThumbnail(Attachment attachment) {
    final imageUrl = widget.apiService.resolveFileUrl(attachment.fileUrl);
    
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Stack(
        children: [
          Container(
            constraints: const BoxConstraints(
              maxWidth: 200,
              maxHeight: 200,
              minWidth: 150,
              minHeight: 100,
            ),
            child: Image.network(
              imageUrl,
              fit: BoxFit.cover,
              loadingBuilder: (context, child, loadingProgress) {
                if (loadingProgress == null) return child;
                return Container(
                  width: 150,
                  height: 100,
                  color: Colors.grey[200],
                  child: Center(
                    child: CircularProgressIndicator(
                      value: loadingProgress.expectedTotalBytes != null
                          ? loadingProgress.cumulativeBytesLoaded /
                              loadingProgress.expectedTotalBytes!
                          : null,
                    ),
                  ),
                );
              },
              errorBuilder: (context, error, stackTrace) {
                return _buildFileAttachment(
                  attachment,
                  path.extension(attachment.fileName).toLowerCase(),
                  true,
                  false,
                );
              },
            ),
          ),
          Positioned(
            top: 8,
            right: 8,
            child: Container(
              padding: const EdgeInsets.all(4),
              decoration: BoxDecoration(
                color: Colors.black.withOpacity(0.6),
                borderRadius: BorderRadius.circular(12),
              ),
              child: const Icon(
                CupertinoIcons.eye,
                color: Colors.white,
                size: 16,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFileAttachment(Attachment attachment, String fileExtension, bool isImage, bool isPdf) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.05),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: _getFileIconColor(fileExtension).withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Icon(
              _getFileIcon(fileExtension),
              color: _getFileIconColor(fileExtension),
              size: 24,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  attachment.fileName,
                  style: const TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: Colors.black87,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  isImage ? 'Image • Tap to view' :
                  isPdf ? 'PDF Document • Tap to view' :
                  'File • Tap to view',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          Icon(
            CupertinoIcons.eye,
            color: Colors.grey[600],
            size: 18,
          ),
        ],
      ),
    );
  }

  IconData _getFileIcon(String extension) {
    switch (extension) {
      case '.jpg':
      case '.jpeg':
      case '.png':
      case '.gif':
      case '.bmp':
      case '.webp':
        return CupertinoIcons.photo;
      case '.pdf':
        return CupertinoIcons.doc_text;
      default:
        return CupertinoIcons.doc;
    }
  }

  Color _getFileIconColor(String extension) {
    switch (extension) {
      case '.jpg':
      case '.jpeg':
      case '.png':
      case '.gif':
      case '.bmp':
      case '.webp':
        return Colors.blue;
      case '.pdf':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  void _showFilePreview(Attachment attachment) {
    showDialog(
      context: context,
      builder: (context) => FilePreviewDialog(
        attachment: attachment,
        apiService: widget.apiService,
      ),
    );
  }



  Widget _buildMessageComposer() {
    return Container(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 8),
      child: Column(
        children: [
          // File attachment preview
          if (_selectedFile != null)
            Container(
              margin: const EdgeInsets.only(bottom: 8),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey[300]!),
              ),
              child: Row(
                children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: _selectedFileType == 'image'
                          ? Colors.blue.withOpacity(0.1)
                          : Colors.red.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(
                      _selectedFileType == 'image'
                          ? CupertinoIcons.photo
                          : CupertinoIcons.doc_text,
                      color: _selectedFileType == 'image' ? Colors.blue : Colors.red,
                      size: 20,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          _selectedFileName,
                          style: const TextStyle(
                            fontWeight: FontWeight.w500,
                            fontSize: 14,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          _selectedFileType == 'image' ? 'Image' : 'Document',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: Icon(CupertinoIcons.xmark_circle_fill, color: Colors.grey[600]),
                    onPressed: _clearSelectedFile,
                    constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                    padding: EdgeInsets.zero,
                  ),
                ],
              ),
            ),

          // Message input row
          Row(
            children: [
              Expanded(
                child: Container(
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(25),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.1),
                        blurRadius: 4,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Row(
                    children: [
                      IconButton(
                        icon: Icon(CupertinoIcons.smiley, color: Colors.grey[600]),
                        onPressed: () {},
                      ),
                      Expanded(
                        child: TextField(
                          controller: _controller,
                          maxLines: null,
                          decoration: InputDecoration(
                            hintText: _selectedFile != null
                                ? 'Add a message...'
                                : 'Type a message',
                            hintStyle: const TextStyle(color: Colors.grey),
                            border: InputBorder.none,
                            contentPadding: const EdgeInsets.symmetric(vertical: 12),
                          ),
                          style: const TextStyle(fontSize: 16),
                        ),
                      ),
                      IconButton(
                        icon: Icon(CupertinoIcons.paperclip, color: Colors.grey[600]),
                        onPressed: _pickFile,
                      ),
                      IconButton(
                        icon: Icon(CupertinoIcons.camera, color: Colors.grey[600]),
                        onPressed: _pickImage,
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Container(
                width: 45,
                height: 45,
                decoration: BoxDecoration(
                  color: (_controller.text.isNotEmpty || _selectedFile != null) ? const Color(0xFF25D366) : Colors.grey[400],
                  borderRadius: BorderRadius.circular(22.5),
                ),
                child: IconButton(
                  onPressed: (_controller.text.isNotEmpty || _selectedFile != null) ? _sendMessage : null,
                  icon: const Icon(
                    CupertinoIcons.paperplane_fill,
                    color: Colors.white,
                    size: 20,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final yesterday = today.subtract(const Duration(days: 1));
    final messageDate = DateTime(timestamp.year, timestamp.month, timestamp.day);

    if (messageDate == today) {
      // Today: show time (HH:MM)
      return '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}';
    } else if (messageDate == yesterday) {
      // Yesterday: show "Yesterday"
      return 'Yesterday';
    } else if (now.difference(timestamp).inDays < 7) {
      // This week: show day name
      const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      return weekdays[timestamp.weekday - 1];
    } else {
      // Older: show date (DD/MM)
      return '${timestamp.day.toString().padLeft(2, '0')}/${timestamp.month.toString().padLeft(2, '0')}';
    }
  }

  String _formatFullTimestamp(DateTime timestamp) {
    return '${timestamp.day.toString().padLeft(2, '0')}/${timestamp.month.toString().padLeft(2, '0')}/${timestamp.year} '
           '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}:${timestamp.second.toString().padLeft(2, '0')}';
  }
}
