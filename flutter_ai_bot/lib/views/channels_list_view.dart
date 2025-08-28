import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/models/channel_model.dart';
import 'package:flutter_ai_bot/views/chat_view.dart';
import 'package:flutter_ai_bot/views/create_channel_view.dart';
import 'package:flutter_ai_bot/views/channel_management_view.dart';

class ChannelsListView extends StatefulWidget {
  final ApiService apiService;

  const ChannelsListView({super.key, required this.apiService});

  @override
  _ChannelsListViewState createState() => _ChannelsListViewState();
}

class _ChannelsListViewState extends State<ChannelsListView> {
  List<Channel> _channels = [];
  bool _isLoading = true;
  bool _isAdmin = false; // This should be fetched from user data

  @override
  void initState() {
    super.initState();
    _loadChannels();
    _checkAdminStatus();
  }

  Future<void> _loadChannels() async {
    try {
      final channels = await widget.apiService.getChannels();
      setState(() {
        _channels = channels;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load channels: $e')),
      );
    }
  }

  Future<void> _checkAdminStatus() async {
    // In a real app, you'd check user permissions from the API
    // For now, we'll assume admin status based on user ID or role
    setState(() {
      _isAdmin = true; // Simulate admin status
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xff023E8A), // Primary deep blue for app bar
        elevation: 0,
        title: const Text(
          'Channels',
          style: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: false,
        actions: [
          if (_isAdmin)
            IconButton(
              icon: const Icon(CupertinoIcons.settings, color: Colors.white),
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => ChannelManagementView(
                      apiService: widget.apiService,
                    ),
                  ),
                );
              },
            ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadChannels,
              child: _channels.isEmpty
                  ? _buildEmptyState()
                  : ListView.builder(
                      padding: const EdgeInsets.symmetric(vertical: 8),
                      itemCount: _channels.length,
                      itemBuilder: (context, index) {
                        final channel = _channels[index];
                        return _buildChannelItem(channel);
                      },
                    ),
            ),
      floatingActionButton: _isAdmin
          ? FloatingActionButton(
              onPressed: () async {
                final result = await Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => CreateChannelView(
                      apiService: widget.apiService,
                    ),
                  ),
                );
                if (result == true) {
                  _loadChannels();
                }
              },
              backgroundColor: const Color(0xff00B4D8), // Bright accent for floating action button
              child: const Icon(CupertinoIcons.add, color: Colors.white),
            )
          : null,
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Container(
            width: 80,
            height: 80,
            decoration: BoxDecoration(
              color: const Color(0xff48CAE4).withOpacity(0.2), // Soft blue background
              borderRadius: BorderRadius.circular(40),
            ),
            child: const Icon(
              CupertinoIcons.chat_bubble_2,
              color: Color(0xff48CAE4), // Soft blue for icon
              size: 40,
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'No channels yet',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              color: Color(0xFF1F2937),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            _isAdmin
                ? 'Create your first channel to start collaborating'
                : 'Ask an admin to create channels or add you to existing ones',
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 16,
              color: Color(0xFF6B7280),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildChannelItem(Channel channel) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        leading: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: const Color(0xff48CAE4).withOpacity(0.2), // Soft blue background
            borderRadius: BorderRadius.circular(25),
          ),
          child: Center(
            child: Text(
              channel.name.isNotEmpty ? channel.name[0].toUpperCase() : '#',
              style: const TextStyle(
                color: Color(0xff48CAE4), // Soft blue for channel avatar text
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        title: Text(
          channel.name,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: Color(0xFF1F2937),
          ),
        ),
        subtitle: Text(
          channel.description.isNotEmpty
              ? channel.description
              : 'Tap to start chatting',
          style: const TextStyle(
            fontSize: 14,
            color: Color(0xFF6B7280),
          ),
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(
              CupertinoIcons.chevron_right,
              color: Color(0xFF9CA3AF),
              size: 16,
            ),
          ],
        ),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ChatView(
                channel: channel,
                apiService: widget.apiService,
              ),
            ),
          );
        },
      ),
    );
  }
}
