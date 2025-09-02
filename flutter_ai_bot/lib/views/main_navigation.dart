import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/views/dashboard_view.dart';
import 'package:flutter_ai_bot/views/channels_list_view.dart';
import 'package:flutter_ai_bot/views/settings_view.dart';

class NavigationItem {
  final IconData icon;
  final String label;
  final Widget page;

  NavigationItem({
    required this.icon,
    required this.label,
    required this.page,
  });
}

class MainNavigation extends StatefulWidget {
  final ApiService apiService;
  final int initialIndex;

  const MainNavigation({super.key, required this.apiService, this.initialIndex = 0});

  @override
  MainNavigationState createState() => MainNavigationState();
}

class MainNavigationState extends State<MainNavigation> {
  late int _currentIndex;
  late List<Widget> _pages;
  late List<NavigationItem> _navigationItems;
  bool _isAdmin = false;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _checkUserRole();
  }

  Future<void> _checkUserRole() async {
    try {
      final isAdmin = await widget.apiService.isCurrentUserAdmin();
      setState(() {
        _isAdmin = isAdmin;
        _setupNavigation();
        _isLoading = false;
      });
    } catch (e) {
      debugPrint('Error checking user role: $e');
      setState(() {
        _isAdmin = false;
        _setupNavigation();
        _isLoading = false;
      });
    }
  }

  void _setupNavigation() {
    _navigationItems = [];
    _pages = [];

    // Add Dashboard only for admin users
    if (_isAdmin) {
      _navigationItems.add(NavigationItem(
        icon: CupertinoIcons.home,
        label: 'Dashboard',
        page: DashboardView(apiService: widget.apiService),
      ));
    }

    // Add Channels for all users
    _navigationItems.add(NavigationItem(
      icon: CupertinoIcons.chat_bubble_2,
      label: 'Channels',
      page: ChannelsListView(apiService: widget.apiService),
    ));

    // Add Settings for all users
    _navigationItems.add(NavigationItem(
      icon: CupertinoIcons.settings,
      label: 'Settings',
      page: SettingsView(apiService: widget.apiService),
    ));

    _pages = _navigationItems.map((item) => item.page).toList();

    // Adjust current index based on admin status
    int targetIndex = widget.initialIndex;
    if (!_isAdmin) {
      // For non-admin users: 0=Channels, 1=Settings
      if (targetIndex == 0) {
        targetIndex = 0; // Channels
      } else if (targetIndex == 1) {
        targetIndex = 0; // Channels (dashboard not available)
      } else {
        targetIndex = 1; // Settings
      }
    }
    // For admin users: 0=Dashboard, 1=Channels, 2=Settings (no adjustment needed)

    _currentIndex = targetIndex.clamp(0, _pages.length - 1);
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.1),
              blurRadius: 10,
              offset: const Offset(0, -2),
            ),
          ],
        ),
        child: SafeArea(
          child: SizedBox(
            height: 60,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: _navigationItems.asMap().entries.map((entry) {
                final index = entry.key;
                final item = entry.value;
                return _buildTabItem(
                  icon: item.icon,
                  label: item.label,
                  index: index,
                );
              }).toList(),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTabItem({
    required IconData icon,
    required String label,
    required int index,
  }) {
    final isSelected = _currentIndex == index;
    return GestureDetector(
      onTap: () {
        setState(() {
          _currentIndex = index;
        });
      },
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              icon,
              color: isSelected ? const Color(0xff0077B6) : Colors.grey, // Primary mid blue for selected tab
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              label,
              style: TextStyle(
                color: isSelected ? const Color(0xff0077B6) : Colors.grey, // Primary mid blue for selected tab text
                fontSize: 12,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
