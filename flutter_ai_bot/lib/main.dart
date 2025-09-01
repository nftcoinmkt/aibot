import 'package:flutter/material.dart';
import 'package:flutter_ai_bot/views/forgot_password_view.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/views/main_navigation.dart';
import 'package:flutter_ai_bot/views/login_view.dart';
import 'package:flutter_ai_bot/views/signup_view.dart';
import 'package:flutter_ai_bot/views/create_channel_view.dart';
import 'package:flutter_ai_bot/views/invite_member_view.dart';
import 'package:flutter_ai_bot/views/change_password_view.dart';
import 'package:flutter_ai_bot/views/reset_password_view.dart';
import 'package:flutter_ai_bot/views/access_denied_view.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}



class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  late final ApiService apiService;

  @override
  void initState() {
    super.initState();
    apiService = ApiService();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter AI Bot',
      theme: ThemeData(
        primaryColor: const Color(0xff023E8A), // Primary deep blue
        scaffoldBackgroundColor: const Color(0xffCAF0F8), // Off-white with blue tint
        colorScheme: ColorScheme.fromSwatch().copyWith(
          primary: const Color(0xff023E8A), // Primary deep blue
          secondary: const Color(0xff00B4D8), // Bright accent for CTAs
          background: const Color(0xffCAF0F8), // Off-white with blue tint
          surface: const Color(0xffADE8F4), // Very light blue for cards
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xff023E8A), // Primary deep blue for headers
          elevation: 0,
          titleTextStyle: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w500,
          ),
          iconTheme: IconThemeData(
            color: Colors.white,
          ),
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xff0077B6), // Primary mid blue for main buttons
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
            ),
          ),
        ),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: BorderSide.none,
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
            borderSide: const BorderSide(color: Color(0xff48CAE4)), // Soft blue for input borders
          ),
        ),
        floatingActionButtonTheme: const FloatingActionButtonThemeData(
          backgroundColor: Color(0xff00B4D8), // Bright accent for floating actions
          foregroundColor: Colors.white,
        ),
        textTheme: const TextTheme(
          bodyLarge: TextStyle(color: Colors.black87),
          bodyMedium: TextStyle(color: Colors.black54),
          titleLarge: TextStyle(color: Colors.black87, fontWeight: FontWeight.bold),
        ),
      ),
      home: FutureBuilder<bool>(
        future: apiService.tryLoadToken(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Scaffold(
              body: Center(
                child: CircularProgressIndicator(),
              ),
            );
          }
          if (snapshot.hasData && snapshot.data == true) {
            return MainNavigation(apiService: apiService);
          } else {
            return LoginView(apiService: apiService);
          }
        },
      ),
      routes: {
        '/login': (context) => LoginView(apiService: apiService),
        '/signup': (context) => SignupView(apiService: apiService),
        '/forgot-password': (context) => ForgotPasswordView(apiService: apiService),
        '/home': (context) => MainNavigation(apiService: apiService),
        '/dashboard': (context) => FutureBuilder<bool>(
          future: apiService.isCurrentUserAdmin(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }
            if (snapshot.hasData && snapshot.data == true) {
              return MainNavigation(apiService: apiService, initialIndex: 0);
            } else {
              return const AccessDeniedView(
                title: 'Admin Access Required',
                message: 'The dashboard is only available to administrators. Please contact your admin for access.',
              );
            }
          },
        ),
        '/channels': (context) => FutureBuilder<bool>(
          future: apiService.isCurrentUserAdmin(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }
            // For admin users: Dashboard=0, Channels=1
            // For regular users: Channels=0
            final channelsIndex = (snapshot.hasData && snapshot.data == true) ? 1 : 0;
            return MainNavigation(apiService: apiService, initialIndex: channelsIndex);
          },
        ),
        '/create-channel': (context) => CreateChannelView(apiService: apiService),
        '/change-password': (context) => ChangePasswordView(apiService: apiService),
        '/reset-password': (context) {
          final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
          final token = args != null ? (args['token'] as String? ?? '') : '';
          return ResetPasswordView(apiService: apiService, initialToken: token.isNotEmpty ? token : null);
        },
        '/invite-member': (context) {
          final args = ModalRoute.of(context)?.settings.arguments as Map<String, dynamic>?;
          final tenant = args != null ? (args['tenant'] as String? ?? '') : '';
          return InviteMemberView(apiService: apiService, fixedTenantName: tenant);
        },
      },
      onGenerateRoute: (settings) {
        final name = settings.name ?? '';
        if (name.startsWith('/reset-password')) {
          final uri = Uri.parse(name);
          final token = uri.queryParameters['token'];
          return MaterialPageRoute(
            builder: (context) => ResetPasswordView(
              apiService: apiService,
              initialToken: token,
            ),
            settings: settings,
          );
        }
        if (name.startsWith('/invite-member')) {
          final uri = Uri.parse(name);
          final tenant = uri.queryParameters['tenant'] ?? '';
          return MaterialPageRoute(
            builder: (context) => InviteMemberView(
              apiService: apiService,
              fixedTenantName: tenant,
            ),
            settings: settings,
          );
        }
        return null;
      },
    );
  }
}

