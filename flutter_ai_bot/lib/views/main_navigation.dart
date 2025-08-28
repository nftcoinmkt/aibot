import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/views/dashboard_view.dart';
import 'package:flutter_ai_bot/views/channels_list_view.dart';
import 'package:flutter_ai_bot/views/settings_view.dart';

class MainNavigation extends StatefulWidget {
  final ApiService apiService;
  final int initialIndex;

  const MainNavigation({super.key, required this.apiService, this.initialIndex = 0});

  @override
  _MainNavigationState createState() => _MainNavigationState();
}

class _MainNavigationState extends State<MainNavigation> {
  late int _currentIndex;

  late List<Widget> _pages;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialIndex;
    _pages = [
      DashboardView(apiService: widget.apiService),
      ChannelsListView(apiService: widget.apiService),
      SettingsView(apiService: widget.apiService),
    ];
  }

  @override
  Widget build(BuildContext context) {
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
          child: Container(
            height: 60,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildTabItem(
                  icon: CupertinoIcons.home,
                  label: 'Dashboard',
                  index: 0,
                ),
                _buildTabItem(
                  icon: CupertinoIcons.chat_bubble_2,
                  label: 'Channels',
                  index: 1,
                ),
                _buildTabItem(
                  icon: CupertinoIcons.settings,
                  label: 'Settings',
                  index: 2,
                ),
              ],
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
