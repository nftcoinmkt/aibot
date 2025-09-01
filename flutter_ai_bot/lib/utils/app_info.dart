import 'package:package_info_plus/package_info_plus.dart';

class AppInfo {
  static PackageInfo? _packageInfo;

  static Future<void> initialize() async {
    _packageInfo = await PackageInfo.fromPlatform();
  }

  static String get appName => _packageInfo?.appName ?? 'Flutter AI Bot';
  static String get version => _packageInfo?.version ?? '1.0.0';
  static String get buildNumber => _packageInfo?.buildNumber ?? '1';
  static String get packageName => _packageInfo?.packageName ?? 'com.example.flutter_ai_bot';

  static String get fullVersion => '$version (Build $buildNumber)';

  static Map<String, String> get appDetails => {
    'App Name': appName,
    'Version': version,
    'Build Number': buildNumber,
    'Package Name': packageName,
  };
}
