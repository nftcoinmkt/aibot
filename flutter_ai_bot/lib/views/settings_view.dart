import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/utils/role_manager.dart';
import 'package:flutter_ai_bot/utils/app_info.dart';
import 'package:flutter_ai_bot/models/user_model.dart';
import 'package:url_launcher/url_launcher.dart';

class SettingsView extends StatefulWidget {
  final ApiService apiService;

  const SettingsView({super.key, required this.apiService});

  @override
  SettingsViewState createState() => SettingsViewState();
}

class SettingsViewState extends State<SettingsView> {
  // Settings values
  bool _darkModeEnabled = false;
  String _selectedLanguage = 'English';
  bool _notificationsEnabled = true;
  bool _dataUsageOptimized = false;
  bool _backupEnabled = true;
  User? _currentUser;
  bool _isLoading = true;
  Map<String, bool> _settingsVisibility = {};

  @override
  void initState() {
    super.initState();
    _loadUserData();
  }

  Future<void> _loadUserData() async {
    try {
      final user = await widget.apiService.getCurrentUser();
      setState(() {
        _currentUser = user;
        _settingsVisibility = RoleManager.getSettingsVisibility(user);
        _isLoading = false;
      });
    } catch (e) {
      debugPrint('Error loading user data: $e');
      setState(() {
        _isLoading = false;
        // Set default visibility for non-authenticated users
        _settingsVisibility = RoleManager.getSettingsVisibility(null);
      });
    }
  }
  void _launchURL(String url) async {
    final Uri uri = Uri.parse(url);
    if (!await launchUrl(uri)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not launch $url'),
        ),
      );
    }
  }

  // Method to check if an element should be visible
  bool _isVisible(String key) {
    return _settingsVisibility[key] ?? false;
  }



  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xff023E8A), // Primary deep blue for app bar
        elevation: 0,
        title: Row(
          children: [
            const Text(
              'Settings',
              style: TextStyle(
                color: Colors.white,
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            if (RoleManager.isAdmin(_currentUser)) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.orange,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  'ADMIN',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
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
                  if (_isVisible('profile_section')) ...[
                    _buildProfileSection(),
                    const SizedBox(height: 20),
                  ],
                  if (_isVisible('settings_section')) ...[
                    _buildSettingsSection(),
                    const SizedBox(height: 20),
                  ],
                  if (_isVisible('about_section')) ...[
                    _buildAboutSection(),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildProfileSection() {
    return Container(
      padding: const EdgeInsets.all(20),
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
      child: Row(
        children: [
          if (_isVisible('profile_avatar'))
            Container(
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: const Color(0xff48CAE4).withOpacity(0.2), // Soft blue background
                borderRadius: BorderRadius.circular(30),
              ),
              child: const Icon(
                CupertinoIcons.person_circle,
                color: Color(0xff48CAE4), // Soft blue for profile icon
                size: 40,
              ),
            ),
          if (_isVisible('profile_avatar')) const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (_isVisible('profile_name'))
                  Row(
                    children: [
                      Text(
                        _currentUser?.fullName ?? 'Loading...',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1F2937),
                        ),
                      ),
                      if (RoleManager.isAdmin(_currentUser)) ...[
                        const SizedBox(width: 8),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: Colors.orange,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Text(
                            RoleManager.getRoleDisplayName(_currentUser?.role ?? 'user').toUpperCase(),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                if (_isVisible('profile_name') && _isVisible('profile_email'))
                  const SizedBox(height: 4),
                if (_isVisible('profile_email'))
                  Text(
                    _currentUser?.email ?? 'Loading...',
                    style: const TextStyle(
                      fontSize: 14,
                      color: Color(0xFF6B7280),
                    ),
                  ),
              ],
            ),
          ),
          if (_isVisible('profile_edit_button'))
            const Icon(
              CupertinoIcons.chevron_right,
              color: Color(0xFF9CA3AF),
              size: 16,
            ),
        ],
      ),
    );
  }

  Widget _buildSettingsSection() {
    List<Widget> settingsItems = [];

    if (_isVisible('notifications')) {
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.bell,
        title: 'Notifications',
        subtitle: 'Manage notification preferences',
        onTap: () {},
        trailing: Switch(
          value: _notificationsEnabled,
          onChanged: (value) {
            setState(() {
              _notificationsEnabled = value;
            });
          },
          activeColor: const Color(0xff0077B6),
        ),
      ));
    }

    if (_isVisible('privacy_security')) {
      if (settingsItems.isNotEmpty) settingsItems.add(const Divider(height: 1));
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.lock,
        title: 'Privacy & Security',
        subtitle: 'Control your privacy settings',
        onTap: () {},
      ));
    }

    if (_isVisible('change_password')) {
      if (settingsItems.isNotEmpty) settingsItems.add(const Divider(height: 1));
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.lock_shield,
        title: 'Change Password',
        subtitle: 'Update your password',
        onTap: () {
          Navigator.of(context).pushNamed('/change-password');
        },
      ));
    }

    if (_isVisible('dark_mode')) {
      if (settingsItems.isNotEmpty) settingsItems.add(const Divider(height: 1));
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.moon,
        title: 'Dark Mode',
        subtitle: 'Switch to dark theme',
        onTap: () {},
        trailing: Switch(
          value: _darkModeEnabled,
          onChanged: (value) {
            setState(() {
              _darkModeEnabled = value;
            });
          },
          activeColor: const Color(0xff0077B6),
        ),
      ));
    }

    if (_isVisible('language')) {
      if (settingsItems.isNotEmpty) settingsItems.add(const Divider(height: 1));
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.globe,
        title: 'Language',
        subtitle: _selectedLanguage,
        onTap: () => _showLanguageSelector(),
      ));
    }

    if (_isVisible('data_usage')) {
      if (settingsItems.isNotEmpty) settingsItems.add(const Divider(height: 1));
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.chart_bar,
        title: 'Data Usage',
        subtitle: 'Optimize data consumption',
        onTap: () {},
        trailing: Switch(
          value: _dataUsageOptimized,
          onChanged: (value) {
            setState(() {
              _dataUsageOptimized = value;
            });
          },
          activeColor: const Color(0xff0077B6),
        ),
      ));
    }

    if (_isVisible('admin_controls') && RoleManager.isAdmin(_currentUser)) {
      if (settingsItems.isNotEmpty) settingsItems.add(const Divider(height: 1));
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.gear_alt,
        title: 'Admin Controls',
        subtitle: 'Manage users and system settings',
        onTap: () {
          // Navigate to admin panel or show admin options
          _showAdminOptions();
        },
      ));
    }

    if (_isVisible('backup_sync')) {
      if (settingsItems.isNotEmpty) settingsItems.add(const Divider(height: 1));
      settingsItems.add(_buildSettingsItem(
        icon: CupertinoIcons.cloud,
        title: 'Backup & Sync',
        subtitle: 'Sync your data across devices',
        onTap: () {},
        trailing: Switch(
          value: _backupEnabled,
          onChanged: (value) {
            setState(() {
              _backupEnabled = value;
            });
          },
          activeColor: const Color(0xff0077B6),
        ),
      ));
    }

    if (settingsItems.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
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
      child: Column(children: settingsItems),
    );
  }

  Widget _buildAboutSection() {
    List<Widget> aboutItems = [];

    if (_isVisible('about_app')) {
      aboutItems.add(_buildSettingsItem(
        icon: CupertinoIcons.info_circle,
        title: 'About',
        subtitle: 'App version and information',
        onTap: () => _showAboutDialog(),
      ));
    }

    if (_isVisible('help_support')) {
      if (aboutItems.isNotEmpty) aboutItems.add(const Divider(height: 1));
      aboutItems.add(_buildSettingsItem(
        icon: CupertinoIcons.question_circle,
        title: 'Help & Support',
        subtitle: 'Get help and contact support',
        onTap: () {},
      ));
    }

    if (_isVisible('privacy_policy')) {
      if (aboutItems.isNotEmpty) aboutItems.add(const Divider(height: 1));
      aboutItems.add(_buildSettingsItem(
        icon: CupertinoIcons.shield_lefthalf_fill,
        title: 'Privacy Policy',
        subtitle: 'Read our privacy policy',
        onTap: () => _launchURL('https://hippocampus-8d4f4f.webflow.io/privacy'),
      ));
    }

    if (_isVisible('terms_service')) {
      if (aboutItems.isNotEmpty) aboutItems.add(const Divider(height: 1));
      aboutItems.add(_buildSettingsItem(
        icon: CupertinoIcons.doc_text,
        title: 'Terms of Service',
        subtitle: 'Read our terms of service',
        onTap: () => _launchURL('https://hippocampus-8d4f4f.webflow.io/terms'),
      ));
    }

    if (_isVisible('app_version')) {
      if (aboutItems.isNotEmpty) aboutItems.add(const Divider(height: 1));
      aboutItems.add(_buildSettingsItem(
        icon: CupertinoIcons.info,
        title: 'App Version',
        subtitle: AppInfo.fullVersion,
        onTap: () {},
        trailing: const SizedBox.shrink(),
      ));
    }

    if (_isVisible('sign_out')) {
      if (aboutItems.isNotEmpty) aboutItems.add(const Divider(height: 1));
      aboutItems.add(_buildSettingsItem(
        icon: CupertinoIcons.square_arrow_right,
        title: 'Sign Out',
        subtitle: 'Sign out of your account',
        onTap: () async {
          final confirmed = await showDialog<bool>(
            context: context,
            builder: (context) => AlertDialog(
              title: const Text('Sign Out'),
              content: const Text('Are you sure you want to sign out?'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(context, false),
                  child: const Text('Cancel'),
                ),
                TextButton(
                  onPressed: () => Navigator.pop(context, true),
                  style: TextButton.styleFrom(foregroundColor: Colors.red),
                  child: const Text('Sign Out'),
                ),
              ],
            ),
          );

          if (confirmed == true) {
            await widget.apiService.signout();
            if (!mounted) return;
            Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
          }
        },
        textColor: Colors.red,
      ));
    }

    if (aboutItems.isEmpty) {
      return const SizedBox.shrink();
    }

    return Container(
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
      child: Column(children: aboutItems),
    );
  }

  // Language selector dialog
  void _showLanguageSelector() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Language'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            'English',
            'Spanish',
            'French',
            'German',
            'Chinese',
            'Japanese',
          ].map((language) => RadioListTile<String>(
            title: Text(language),
            value: language,
            groupValue: _selectedLanguage,
            onChanged: (value) {
              setState(() {
                _selectedLanguage = value!;
              });
              Navigator.pop(context);
            },
          )).toList(),
        ),
      ),
    );
  }

  // About dialog
  void _showAboutDialog() {
    showAboutDialog(
      context: context,
      applicationName: AppInfo.appName,
      applicationVersion: AppInfo.fullVersion,
      applicationIcon: Container(
        width: 60,
        height: 60,
        decoration: BoxDecoration(
          color: const Color(0xff48CAE4).withOpacity(0.2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Icon(
          CupertinoIcons.chat_bubble_2,
          color: Color(0xff48CAE4),
          size: 30,
        ),
      ),
      children: [
        const Text('A powerful AI-powered chat application built with Flutter.'),
        const SizedBox(height: 16),
        Text('Package: ${AppInfo.packageName}'),
        const SizedBox(height: 8),
        const Text('© 2024 Flutter AI Bot. All rights reserved.'),
      ],
    );
  }

  // Admin options dialog
  void _showAdminOptions() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => Container(
        height: MediaQuery.of(context).size.height * 0.6,
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Text(
                  'Admin Controls',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: Colors.orange,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Text(
                    'ADMIN ONLY',
                    style: TextStyle(
                      color: Colors.white,
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView(
                children: [
                  _buildAdminOption(
                    icon: CupertinoIcons.person_2,
                    title: 'User Management',
                    subtitle: 'Manage user accounts and permissions',
                    onTap: () {
                      Navigator.pop(context);
                      // Navigate to user management
                    },
                  ),
                  _buildAdminOption(
                    icon: CupertinoIcons.chat_bubble_2,
                    title: 'Channel Management',
                    subtitle: 'Create and manage channels',
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.pushNamed(context, '/create-channel');
                    },
                  ),
                  _buildAdminOption(
                    icon: CupertinoIcons.person_add,
                    title: 'Invite Members',
                    subtitle: 'Invite new team members',
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.pushNamed(context, '/invite-member');
                    },
                  ),
                  _buildAdminOption(
                    icon: CupertinoIcons.chart_bar,
                    title: 'Analytics',
                    subtitle: 'View usage statistics and reports',
                    onTap: () {
                      Navigator.pop(context);
                      // Navigate to analytics
                    },
                  ),
                  _buildAdminOption(
                    icon: CupertinoIcons.gear_alt,
                    title: 'System Settings',
                    subtitle: 'Configure system-wide settings',
                    onTap: () {
                      Navigator.pop(context);
                      // Navigate to system settings
                    },
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAdminOption({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: const Color(0xff0077B6).withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(
            icon,
            color: const Color(0xff0077B6),
            size: 20,
          ),
        ),
        title: Text(
          title,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
          ),
        ),
        subtitle: Text(
          subtitle,
          style: const TextStyle(
            fontSize: 14,
            color: Color(0xFF6B7280),
          ),
        ),
        trailing: const Icon(
          CupertinoIcons.chevron_right,
          color: Color(0xFF9CA3AF),
          size: 16,
        ),
        onTap: onTap,
      ),
    );
  }

  Widget _buildSettingsItem({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    Widget? trailing,
    Color? textColor,
  }) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: Container(
        width: 40,
        height: 40,
        decoration: BoxDecoration(
          color: (textColor ?? const Color(0xff48CAE4)).withOpacity(0.2), // Soft blue background
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(
          icon,
          color: textColor ?? const Color(0xff48CAE4), // Soft blue for icons
          size: 20,
        ),
      ),
      title: Text(
        title,
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.w600,
          color: textColor ?? const Color(0xFF1F2937),
        ),
      ),
      subtitle: Text(
        subtitle,
        style: const TextStyle(
          fontSize: 14,
          color: Color(0xFF6B7280),
        ),
      ),
      trailing: trailing ?? const Icon(
        CupertinoIcons.chevron_right,
        color: Color(0xFF9CA3AF),
        size: 16,
      ),
      onTap: onTap,
    );
  }
}
