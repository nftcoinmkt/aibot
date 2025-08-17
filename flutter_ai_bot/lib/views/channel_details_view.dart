import 'package:flutter/material.dart';
import 'package:flutter_ai_bot/models/channel_member_model.dart';
import 'package:flutter_ai_bot/models/channel_model.dart';
import 'package:flutter_ai_bot/models/user_model.dart';
import 'package:flutter_ai_bot/network/api_service.dart';

class ChannelDetailsView extends StatefulWidget {
  final Channel channel;
  final ApiService apiService;

  const ChannelDetailsView({
    super.key,
    required this.channel,
    required this.apiService,
  });

  @override
  _ChannelDetailsViewState createState() => _ChannelDetailsViewState();
}

class _ChannelDetailsViewState extends State<ChannelDetailsView> {
  late Future<List<ChannelMember>> _membersFuture;
  late Future<List<User>> _usersFuture;
  List<User> _channelMembers = [];
  List<User> _availableUsers = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    try {
      final channelMembers = await widget.apiService.getChannelMembers(widget.channel.id);
      final allUsers = await widget.apiService.getUsers();
      
      final memberUserIds = channelMembers.map((m) => m.userId).toSet();
      final availableUsers = allUsers.where((u) => !memberUserIds.contains(u.id)).toList();
      
      // Get user details for channel members
      final membersWithUserDetails = <User>[];
      for (final member in channelMembers) {
        final user = allUsers.firstWhere(
          (u) => u.id == member.userId,
          orElse: () => User(
            id: member.userId,
            email: 'unknown@example.com',
            fullName: 'User ${member.userId}',
            tenantName: '',
            role: 'user',
            isActive: true,
            createdAt: DateTime.now(),
          ),
        );
        membersWithUserDetails.add(user);
      }
      
      setState(() {
        _channelMembers = membersWithUserDetails;
        _availableUsers = availableUsers;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load data: $e')),
      );
    }
  }

  void _addMember(int userId) async {
    try {
      await widget.apiService.addMemberToChannel(widget.channel.id, userId);
      _loadData(); // Reload data to refresh both lists
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Member added successfully')));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to add member: $e')));
    }
  }

  void _removeMember(int userId) async {
    try {
      await widget.apiService.removeMemberFromChannel(widget.channel.id, userId);
      _loadData(); // Reload data to refresh both lists
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Member removed successfully')));
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Failed to remove member: $e')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.channel.name),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Members', style: Theme.of(context).textTheme.headlineSmall),
                  _buildMembersList(),
                  SizedBox(height: 24),
                  Text('Add Members', style: Theme.of(context).textTheme.headlineSmall),
                  _buildUsersList(),
                ],
              ),
            ),
    );
  }

  Widget _buildMembersList() {
    if (_channelMembers.isEmpty) {
      return const Text('No members in this channel.');
    }
    
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _channelMembers.length,
      itemBuilder: (context, index) {
        final user = _channelMembers[index];
        return _buildMemberItem(user, isChannelMember: true);
      },
    );
  }

  Widget _buildUsersList() {
    if (_availableUsers.isEmpty) {
      return const Text('No users available to add.');
    }
    
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: _availableUsers.length,
      itemBuilder: (context, index) {
        final user = _availableUsers[index];
        return _buildMemberItem(user, isChannelMember: false);
      },
    );
  }

  Widget _buildMemberItem(User user, {required bool isChannelMember}) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: CircleAvatar(
        backgroundColor: const Color(0xFF25D366).withOpacity(0.1),
        child: Text(
          user.fullName.isNotEmpty ? user.fullName[0].toUpperCase() : 'U',
          style: const TextStyle(
            color: Color(0xFF25D366),
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      title: Text(
        user.fullName,
        style: const TextStyle(
          fontWeight: FontWeight.w600,
          fontSize: 16,
        ),
      ),
      subtitle: Text(
        user.email,
        style: TextStyle(
          color: Colors.grey[600],
          fontSize: 14,
        ),
      ),
      trailing: IconButton(
        icon: Icon(
          isChannelMember ? Icons.remove_circle_outline : Icons.add_circle_outline,
          color: isChannelMember ? Colors.red : Colors.green,
        ),
        onPressed: () {
          if (isChannelMember) {
            _removeMember(user.id);
          } else {
            _addMember(user.id);
          }
        },
      ),
    );
  }
}
