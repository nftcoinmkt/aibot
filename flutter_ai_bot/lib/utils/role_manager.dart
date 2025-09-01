import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/models/user_model.dart';

class RoleManager {
  static const String adminRole = 'admin';
  static const String superUserRole = 'super_user';
  static const String userRole = 'user';

  /// Check if a user has admin privileges
  static bool isAdmin(User? user) {
    if (user == null) return false;
    return user.role == adminRole || user.role == superUserRole;
  }

  /// Check if a user is a regular user
  static bool isRegularUser(User? user) {
    if (user == null) return true;
    return user.role == userRole;
  }

  /// Get user role display name
  static String getRoleDisplayName(String role) {
    switch (role) {
      case adminRole:
        return 'Administrator';
      case superUserRole:
        return 'Super User';
      case userRole:
        return 'User';
      default:
        return 'Unknown';
    }
  }

  /// Get available features for a user role
  static List<String> getAvailableFeatures(String role) {
    switch (role) {
      case adminRole:
      case superUserRole:
        return [
          'dashboard',
          'channels',
          'settings',
          'user_management',
          'channel_management',
          'invite_members',
          'system_settings',
        ];
      case userRole:
      default:
        return [
          'channels',
          'settings',
          'profile',
        ];
    }
  }

  /// Check if a user can access a specific feature
  static bool canAccessFeature(User? user, String feature) {
    if (user == null) return false;
    final availableFeatures = getAvailableFeatures(user.role);
    return availableFeatures.contains(feature);
  }

  /// Get navigation items based on user role
  static Map<String, bool> getNavigationVisibility(User? user) {
    final isAdminUser = isAdmin(user);
    
    return {
      'dashboard': isAdminUser,
      'channels': true, // Available to all users
      'settings': true, // Available to all users
      'user_management': isAdminUser,
      'channel_management': isAdminUser,
      'admin_settings': isAdminUser,
    };
  }

  /// Get settings page visibility based on user role
  static Map<String, bool> getSettingsVisibility(User? user) {
    final isAdminUser = isAdmin(user);
    
    return {
      // Profile Section - Available to all
      'profile_section': true,
      'profile_avatar': true,
      'profile_name': true,
      'profile_email': true,
      'profile_edit_button': false,
      
      // Settings Section - Mixed access
      'settings_section': true,
      'notifications': false,
      'privacy_security': false,
      'change_password': true,
      'dark_mode': false,
      'language': false,
      'data_usage': false, // Only for regular users
      'backup_sync': false,
      'admin_controls': isAdminUser, // Only for admins
      
      // About Section - Available to all
      'about_section': false,
      'about_app': false,
      'help_support': false,
      'privacy_policy': true,
      'terms_service': false,
      'app_version': true,
      'sign_out': true,
    };
  }
}
