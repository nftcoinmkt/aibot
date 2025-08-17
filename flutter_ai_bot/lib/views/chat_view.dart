import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/models/attachment_model.dart';
import 'package:flutter_ai_bot/models/channel_model.dart';
import 'package:flutter_ai_bot/models/chat_message_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'dart:async';
import 'package:flutter_ai_bot/utils/platform_file_uploader.dart';
import 'package:flutter_ai_bot/views/channel_details_view.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:convert';


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
  bool _isTyping = false;
  bool _isLoading = true;
  final PlatformFileUploader _fileUploader = getPlatformFileUploader();
  int _lastMessageId = 0;

  @override
  void initState() {
    super.initState();
    _currentUserId = widget.apiService.getUserId();
    _loadMessages();

    _controller.addListener(() {
      if (mounted) {
        setState(() {
          _isTyping = _controller.text.isNotEmpty;
        });
      }
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }



  void _loadMessages() async {
    try {
      final historicalMessages = await widget.apiService.getChannelMessages(widget.channel.id);
      if (mounted) {
        setState(() {
          _messages = historicalMessages.reversed.toList();
          if (_messages.isNotEmpty) {
            _lastMessageId = _messages.first.id;
          }
          _isLoading = false;
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

  void _sendMessage() async {
    if (_controller.text.isEmpty) return;
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
      _messages.insert(0, tempMessage);
    });

    try {
      // Send message via API to ensure it's saved
      final messages = await widget.apiService.sendMessageInChannel(widget.channel.id, messageText);

      // Remove the temporary message and add the real messages (user + AI response)
      setState(() {
        final index = _messages.indexWhere((m) => m.id == tempMessage.id);
        if (index != -1) {
          _messages.removeAt(index);
        }

        // Add the messages in chronological order (user message first, then AI response)
        // The ListView is reversed, so newer messages appear at the top
        for (final message in messages) {
          _messages.insert(0, message.copyWith(status: MessageStatus.sent));
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


  void _pickFile() async {
    final tempId = DateTime.now().millisecondsSinceEpoch;
    try {
      await _fileUploader.pickFile(widget.apiService, widget.channel.id, (placeholder) {
        // Add placeholder
        setState(() {
          _messages.insert(0, placeholder);
        });
      }, (finalMessage, tempId) {
        // Replace placeholder with final message or add new message
        setState(() {
          final index = _messages.indexWhere((m) => m.id == tempId);
          if (index != -1) {
            // Replace placeholder with first message (user message)
            _messages[index] = finalMessage;
          } else {
            // Add additional messages (like AI response) at the top
            _messages.insert(0, finalMessage);
          }
        });
      }, (tempId) {
        // Handle failure
        setState(() {
          final index = _messages.indexWhere((m) => m.id == tempId);
          if (index != -1) {
            final failedMessage = _messages[index].copyWith(status: MessageStatus.failed);
            _messages[index] = failedMessage;
          }
        });
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to pick file: $e')),
      );
    }
  }


  void _pickImage() async {
    try {
      await _fileUploader.pickImage(widget.apiService, widget.channel.id, (placeholder) {
        setState(() {
          _messages.insert(0, placeholder);
        });
      }, (finalMessage, tempId) {
        setState(() {
          final index = _messages.indexWhere((m) => m.id == tempId);
          if (index != -1) {
            // Replace placeholder with first message (user message)
            _messages[index] = finalMessage;
          } else {
            // Add additional messages (like AI response) at the top
            _messages.insert(0, finalMessage);
          }
        });
      }, (tempId) {
        setState(() {
          final index = _messages.indexWhere((m) => m.id == tempId);
          if (index != -1) {
            final failedMessage = _messages[index].copyWith(status: MessageStatus.failed);
            _messages[index] = failedMessage;
          }
        });
      }, context);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to pick image: $e')),
      );
    }
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
                    Text(
                      'Online',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.8),
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        actions: [
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
        child: Column(
          children: [
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : ListView.builder(
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
            Container(
              color: Colors.white,
              child: _buildMessageComposer(),
            ),
          ],
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
            child: _buildMessageContent(message, isMe, isAI: isAI),
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
      return 'User'; // Could be enhanced to show actual user names
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
              Text(
                _formatTime(message.timestamp),
                style: TextStyle(
                  color: Colors.grey[600],
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAttachmentView(Attachment attachment) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.black.withOpacity(0.05),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        children: [
          Icon(CupertinoIcons.doc, color: Colors.grey[700], size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              attachment.fileName,
              style: const TextStyle(
                decoration: TextDecoration.underline,
                fontSize: 14,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageComposer() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
      child: SafeArea(
        child: Row(
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
                        decoration: const InputDecoration(
                          hintText: 'Type a message',
                          hintStyle: TextStyle(color: Colors.grey),
                          border: InputBorder.none,
                          contentPadding: EdgeInsets.symmetric(vertical: 12),
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
                color: _isTyping ? const Color(0xFF25D366) : Colors.grey[400],
                borderRadius: BorderRadius.circular(22.5),
              ),
              child: IconButton(
                onPressed: _isTyping ? _sendMessage : null,
                icon: Icon(
                  _isTyping ? CupertinoIcons.paperplane_fill : CupertinoIcons.mic_fill,
                  color: Colors.white,
                  size: 20,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final messageDate = DateTime(timestamp.year, timestamp.month, timestamp.day);
    
    if (messageDate == today) {
      return '${timestamp.hour.toString().padLeft(2, '0')}:${timestamp.minute.toString().padLeft(2, '0')}';
    } else {
      return '${timestamp.day}/${timestamp.month}';
    }
  }
}
