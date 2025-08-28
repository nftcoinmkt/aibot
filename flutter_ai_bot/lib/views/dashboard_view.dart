import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/models/user_model.dart';
import 'package:flutter_ai_bot/models/channel_model.dart';
import 'package:flutter_ai_bot/models/chat_message_model.dart';

class DashboardView extends StatefulWidget {
  final ApiService apiService;

  const DashboardView({super.key, required this.apiService});

  @override
  _DashboardViewState createState() => _DashboardViewState();
}

class _DashboardViewState extends State<DashboardView> {
  User? _currentUser;
  bool _isLoading = true;
  String _welcomeMessage = '';
  List<Channel> _recentChannels = [];
  List<ChatMessage> _recentMessages = [];

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    try {
      // Load recent channels and messages
      final channels = await widget.apiService.getChannels();
      final recentChannels = channels.take(3).toList();

      // Load users to determine current tenant and cache it
      try {
        final users = await widget.apiService.getUsers();
        if (users.isNotEmpty) {
          widget.apiService.setCurrentTenantName(users.first.tenantName);
          _currentUser = users.first;
        }
      } catch (e) {
        // Non-fatal: continue without tenant
        print('Unable to load users for tenant detection: $e');
      }

      // Load recent messages from the first channel if available
      List<ChatMessage> recentMessages = [];
      if (recentChannels.isNotEmpty) {
        try {
          recentMessages = await widget.apiService.getChannelMessages(
            recentChannels.first.id,
            daysBack: 1
          );
          recentMessages = recentMessages.take(5).toList();
        } catch (e) {
          print('Failed to load recent messages: $e');
        }
      }

      setState(() {
        _welcomeMessage = 'Welcome back!';
        _recentChannels = recentChannels;
        _recentMessages = recentMessages;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _welcomeMessage = 'Welcome to the app!';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xff023E8A), // Primary deep blue for app bar
        elevation: 0,
        title: const Text(
          'Dashboard',
          style: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: false,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildWelcomeCard(),
                  const SizedBox(height: 20),
                  _buildQuickActions(),
                  const SizedBox(height: 24),
                  _buildRecentChannels(),
                  const SizedBox(height: 24),
                  _buildRecentActivity(),
                ],
              ),
            ),
    );
  }

  Widget _buildWelcomeCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xff0077B6), Color(0xff0096C7)], // Primary mid blue to secondary blue gradient
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: const Color(0xff0077B6).withOpacity(0.3), // Primary mid blue shadow
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(25),
                ),
                child: const Icon(
                  CupertinoIcons.person_circle,
                  color: Colors.white,
                  size: 30,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _welcomeMessage,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 24,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Ready to collaborate with your team?',
                      style: TextStyle(
                        color: Colors.white.withOpacity(0.9),
                        fontSize: 16,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildQuickActions() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Actions',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1F2937),
          ),
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(
              child: _buildActionCard(
                icon: CupertinoIcons.add_circled,
                title: 'Create Channel',
                subtitle: 'Start a new conversation',
                color: const Color(0xFF3B82F6),
                onTap: () {
                  Navigator.pushNamed(context, '/create-channel');
                },
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _buildActionCard(
                icon: CupertinoIcons.person_add,
                title: 'Invite Members',
                subtitle: 'Add team members',
                color: const Color(0xFF10B981),
                onTap: () {
                  final tenant = widget.apiService.currentTenantName ?? _currentUser?.tenantName ?? '';
                  if (tenant.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Your organization context is not available yet. Please try again in a moment.')),
                    );
                    return;
                  }
                  Navigator.pushNamed(
                    context,
                    '/invite-member',
                    arguments: {'tenant': tenant},
                  );
                },
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildActionCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(12),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 10,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 40,
              height: 40,
              decoration: BoxDecoration(
                color: color.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(
                icon,
                color: color,
                size: 24,
              ),
            ),
            const SizedBox(height: 12),
            Flexible(
              child: Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: Color(0xFF1F2937),
                ),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            const SizedBox(height: 4),
            Flexible(
              child: Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 12,
                  color: Color(0xFF6B7280),
                ),
                overflow: TextOverflow.ellipsis,
                maxLines: 2,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRecentChannels() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Recent Channels',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1F2937),
          ),
        ),
        const SizedBox(height: 12),
        if (_recentChannels.isEmpty)
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: const Center(
              child: Text(
                'No channels yet. Create your first channel!',
                style: TextStyle(
                  color: Color(0xFF6B7280),
                  fontSize: 16,
                ),
              ),
            ),
          )
        else
          ...(_recentChannels.map((channel) => Container(
            margin: const EdgeInsets.only(bottom: 8),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 10,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: ListTile(
              leading: Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: const Color(0xff48CAE4).withOpacity(0.2), // Soft blue background
                  borderRadius: BorderRadius.circular(20),
                ),
                child: const Icon(
                  CupertinoIcons.chat_bubble_2,
                  color: Color(0xff48CAE4), // Soft blue for chat icon
                  size: 20,
                ),
              ),
              title: Text(
                channel.name,
                style: const TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 16,
                ),
              ),
              subtitle: Text(
                channel.description ?? 'No description',
                style: const TextStyle(
                  color: Color(0xFF6B7280),
                  fontSize: 14,
                ),
              ),
              trailing: const Icon(
                CupertinoIcons.chevron_right,
                color: Color(0xFF9CA3AF),
                size: 16,
              ),
              onTap: () {
                Navigator.pushNamed(context, '/channels');
              },
            ),
          ))),
      ],
    );
  }

  Widget _buildRecentActivity() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Recent Messages',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Color(0xFF1F2937),
          ),
        ),
        const SizedBox(height: 12),
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            children: _recentMessages.isEmpty
                ? [
                    _buildActivityItem(
                      icon: CupertinoIcons.chat_bubble_2,
                      title: 'No recent messages',
                      subtitle: 'Start a conversation in a channel',
                      time: '',
                    ),
                  ]
                : _recentMessages.map((message) => _buildActivityItem(
                    icon: message.userId == -1
                        ? CupertinoIcons.gear_alt
                        : CupertinoIcons.person,
                    title: message.userId == -1
                        ? 'AI Bot'
                        : 'You',
                    subtitle: message.message.length > 50
                        ? '${message.message.substring(0, 50)}...'
                        : message.message,
                    time: _formatTime(message.timestamp),
                  )).toList(),
          ),
        ),
      ],
    );
  }

  String _formatTime(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else {
      return '${difference.inDays}d ago';
    }
  }

  Widget _buildActivityItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required String time,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(0xff48CAE4).withOpacity(0.2), // Soft blue background
              borderRadius: BorderRadius.circular(20),
            ),
            child: Icon(
              icon,
              color: const Color(0xff48CAE4), // Soft blue for icons
              size: 20,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: Color(0xFF1F2937),
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: const TextStyle(
                    fontSize: 14,
                    color: Color(0xFF6B7280),
                  ),
                ),
              ],
            ),
          ),
          if (time.isNotEmpty)
            Text(
              time,
              style: const TextStyle(
                fontSize: 12,
                color: Color(0xFF9CA3AF),
              ),
            ),
        ],
      ),
    );
  }
}
