import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/models/channel_model.dart';
import 'package:flutter_ai_bot/models/user_model.dart';

class MemberManagementView extends StatefulWidget {
  final Channel channel;
  final ApiService apiService;

  const MemberManagementView({
    super.key,
    required this.channel,
    required this.apiService,
  });

  @override
  _MemberManagementViewState createState() => _MemberManagementViewState();
}

class _MemberManagementViewState extends State<MemberManagementView> {
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

  Future<void> _addMember(User user) async {
    try {
      await widget.apiService.addMemberToChannel(widget.channel.id, user.id);
      
      setState(() {
        _channelMembers.add(user);
        _availableUsers.removeWhere((u) => u.id == user.id);
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${user.fullName} added to channel')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to add member: $e')),
      );
    }
  }

  Future<void> _removeMember(User user) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remove Member'),
        content: Text('Remove ${user.fullName} from this channel?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Remove'),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        await widget.apiService.removeMemberFromChannel(widget.channel.id, user.id);
        
        setState(() {
          _channelMembers.removeWhere((u) => u.id == user.id);
          _availableUsers.add(user);
        });
        
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('${user.fullName} removed from channel')),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Failed to remove member: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xff023E8A), // Primary deep blue for app bar
        elevation: 0,
        leading: IconButton(
          icon: const Icon(CupertinoIcons.back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Manage Members',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            Text(
              widget.channel.name,
              style: const TextStyle(
                color: Colors.white70,
                fontSize: 14,
              ),
            ),
          ],
        ),
        centerTitle: false,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildMembersSection(),
                  const SizedBox(height: 24),
                  _buildAvailableUsersSection(),
                ],
              ),
            ),
    );
  }

  Widget _buildMembersSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(
              CupertinoIcons.person_2_fill,
              color: Color(0xff48CAE4), // Soft blue for section icon
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              'Channel Members (${_channelMembers.length})',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1F2937),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
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
          child: _channelMembers.isEmpty
              ? const Padding(
                  padding: EdgeInsets.all(20),
                  child: Center(
                    child: Text(
                      'No members in this channel',
                      style: TextStyle(
                        color: Color(0xFF6B7280),
                        fontSize: 16,
                      ),
                    ),
                  ),
                )
              : ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _channelMembers.length,
                  separatorBuilder: (context, index) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final member = _channelMembers[index];
                    return _buildMemberItem(member, isChannelMember: true);
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildAvailableUsersSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            const Icon(
              CupertinoIcons.person_add,
              color: Color(0xFF3B82F6),
              size: 20,
            ),
            const SizedBox(width: 8),
            Text(
              'Add Members (${_availableUsers.length})',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1F2937),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Container(
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
          child: _availableUsers.isEmpty
              ? const Padding(
                  padding: EdgeInsets.all(20),
                  child: Center(
                    child: Text(
                      'All users are already members',
                      style: TextStyle(
                        color: Color(0xFF6B7280),
                        fontSize: 16,
                      ),
                    ),
                  ),
                )
              : ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _availableUsers.length,
                  separatorBuilder: (context, index) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final user = _availableUsers[index];
                    return _buildMemberItem(user, isChannelMember: false);
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildMemberItem(User user, {required bool isChannelMember}) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: CircleAvatar(
        backgroundColor: const Color(0xff48CAE4).withOpacity(0.2), // Soft blue background
        child: Text(
          user.fullName.isNotEmpty ? user.fullName[0].toUpperCase() : 'U',
          style: const TextStyle(
            color: Color(0xff48CAE4), // Soft blue for avatar text
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
      title: Text(
        user.fullName,
        style: const TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: Color(0xFF1F2937),
        ),
      ),
      subtitle: Text(
        user.email,
        style: const TextStyle(
          fontSize: 14,
          color: Color(0xFF6B7280),
        ),
      ),
      trailing: isChannelMember
          ? IconButton(
              onPressed: () => _removeMember(user),
              icon: const Icon(
                CupertinoIcons.minus_circle,
                color: Colors.red,
              ),
            )
          : IconButton(
              onPressed: () => _addMember(user),
              icon: const Icon(
                CupertinoIcons.add_circled,
                color: Color(0xff00B4D8), // Bright accent for add action
              ),
            ),
    );
  }
}
