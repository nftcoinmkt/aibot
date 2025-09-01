import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_ai_bot/utils/role_manager.dart';
import 'package:flutter_ai_bot/models/user_model.dart';

void main() {
  group('RoleManager Tests', () {
    test('should identify admin users correctly', () {
      final adminUser = User(
        id: 1,
        email: 'admin@test.com',
        fullName: 'Admin User',
        tenantName: 'Test Tenant',
        role: 'admin',
        isActive: true,
        createdAt: DateTime.now(),
      );

      final superUser = User(
        id: 2,
        email: 'super@test.com',
        fullName: 'Super User',
        tenantName: 'Test Tenant',
        role: 'super_user',
        isActive: true,
        createdAt: DateTime.now(),
      );

      final regularUser = User(
        id: 3,
        email: 'user@test.com',
        fullName: 'Regular User',
        tenantName: 'Test Tenant',
        role: 'user',
        isActive: true,
        createdAt: DateTime.now(),
      );

      expect(RoleManager.isAdmin(adminUser), true);
      expect(RoleManager.isAdmin(superUser), true);
      expect(RoleManager.isAdmin(regularUser), false);
      expect(RoleManager.isAdmin(null), false);
    });

    test('should return correct navigation visibility for admin', () {
      final adminUser = User(
        id: 1,
        email: 'admin@test.com',
        fullName: 'Admin User',
        tenantName: 'Test Tenant',
        role: 'admin',
        isActive: true,
        createdAt: DateTime.now(),
      );

      final visibility = RoleManager.getNavigationVisibility(adminUser);
      
      expect(visibility['dashboard'], true);
      expect(visibility['channels'], true);
      expect(visibility['settings'], true);
      expect(visibility['user_management'], true);
    });

    test('should return correct navigation visibility for regular user', () {
      final regularUser = User(
        id: 1,
        email: 'user@test.com',
        fullName: 'Regular User',
        tenantName: 'Test Tenant',
        role: 'user',
        isActive: true,
        createdAt: DateTime.now(),
      );

      final visibility = RoleManager.getNavigationVisibility(regularUser);
      
      expect(visibility['dashboard'], false);
      expect(visibility['channels'], true);
      expect(visibility['settings'], true);
      expect(visibility['user_management'], false);
    });

    test('should return correct settings visibility for admin', () {
      final adminUser = User(
        id: 1,
        email: 'admin@test.com',
        fullName: 'Admin User',
        tenantName: 'Test Tenant',
        role: 'admin',
        isActive: true,
        createdAt: DateTime.now(),
      );

      final visibility = RoleManager.getSettingsVisibility(adminUser);
      
      expect(visibility['admin_controls'], true);
      expect(visibility['profile_section'], true);
      expect(visibility['settings_section'], true);
    });

    test('should return correct settings visibility for regular user', () {
      final regularUser = User(
        id: 1,
        email: 'user@test.com',
        fullName: 'Regular User',
        tenantName: 'Test Tenant',
        role: 'user',
        isActive: true,
        createdAt: DateTime.now(),
      );

      final visibility = RoleManager.getSettingsVisibility(regularUser);
      
      expect(visibility['admin_controls'], false);
      expect(visibility['profile_section'], true);
      expect(visibility['settings_section'], true);
    });
  });
}
