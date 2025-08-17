import 'package:flutter/material.dart';
import 'package:flutter_ai_bot/views/forgot_password_view.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:flutter_ai_bot/views/main_navigation.dart';
import 'package:flutter_ai_bot/views/login_view.dart';
import 'package:flutter_ai_bot/views/signup_view.dart';

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
        primaryColor: const Color(0xff075E54),
        scaffoldBackgroundColor: const Color(0xffECE5DD),
        colorScheme: ColorScheme.fromSwatch().copyWith(
          secondary: const Color(0xff25D366),
          background: const Color(0xffECE5DD),
        ),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xff075E54),
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
            backgroundColor: const Color(0xff075E54),
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
            borderSide: const BorderSide(color: Color(0xff075E54)),
          ),
        ),
        floatingActionButtonTheme: const FloatingActionButtonThemeData(
          backgroundColor: Color(0xff25D366),
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
        '/channels': (context) => MainNavigation(apiService: apiService, initialIndex: 1),
        '/create-channel': (context) => MainNavigation(apiService: apiService, initialIndex: 2),
      },
    );
  }
}

