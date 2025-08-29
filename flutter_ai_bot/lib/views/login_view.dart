import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import '../network/api_service.dart';
import 'dart:async';
import 'package:flutter_svg/flutter_svg.dart';

class LoginView extends StatefulWidget {
  final ApiService apiService;

  const LoginView({super.key, required this.apiService});

  @override
  _LoginViewState createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  late final ApiService _apiService;
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;

  // OTP login state
  final _identifierController = TextEditingController();
  final _otpCodeController = TextEditingController();
  bool _useOtpLogin = false;
  bool _isRequestingOtp = false;
  bool _isVerifyingOtp = false;
  int _retryAfter = 0;
  Timer? _resendTimer;

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService;
  }

  void _login() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        final result = await _apiService.loginByIdentifier(
          _emailController.text.trim(),
          _passwordController.text,
        );
        final String token = result['access_token'];
        final int userId = result['user_id'];
        await _apiService.setToken(token, userId: userId);
        print('Login successful');

        // Set current tenant as early as possible for faster availability
        // Prefer the backend-provided tenant name when available
        final dynamic tn = (result['tenant_name'] ?? result['tenant'] ?? result['tenantName']);
        if (tn is String && tn.isNotEmpty) {
          _apiService.setCurrentTenantName(tn);
        } else {
          // Fallback: fetch users and infer tenant
          try {
            final users = await _apiService.getUsers();
            if (users.isNotEmpty) {
              _apiService.setCurrentTenantName(users.first.tenantName);
            }
          } catch (e) {
            // Non-fatal: proceed without tenant set, will be set later in dashboard
            print('Unable to set tenant at login: $e');
          }
        }

        Navigator.pushReplacementNamed(context, '/home');
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to login: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  void _startResendTimer(int seconds) {
    _resendTimer?.cancel();
    setState(() {
      _retryAfter = seconds;
    });
    _resendTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_retryAfter <= 1) {
        setState(() {
          _retryAfter = 0;
        });
        timer.cancel();
      } else {
        setState(() {
          _retryAfter -= 1;
        });
      }
    });
  }

  Future<void> _requestOtpLogin() async {
    final identifier = _identifierController.text.trim();
    if (identifier.isEmpty || identifier.contains('@')) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter your phone number'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isRequestingOtp = true;
    });
    try {
      final resp = await _apiService.requestOtp(
        contactType: 'phone',
        contact: identifier,
        purpose: 'login',
      );
      final bool sent = resp['sent'] == true;
      final int retry = (resp['retry_after'] ?? 30) as int;
      if (sent && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('OTP sent. Please check your phone.'),
            backgroundColor: Color(0xff00B4D8), // Bright accent for notifications
          ),
        );
      }
      _startResendTimer(retry);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to request OTP: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isRequestingOtp = false;
        });
      }
    }
  }

  Future<void> _verifyOtpLogin() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isVerifyingOtp = true;
      });

      try {
        final result = await _apiService.verifyLoginOtp(
          identifier: _identifierController.text.trim(),
          code: _otpCodeController.text.trim(),
        );
        final String token = result['access_token'];
        final int userId = result['user_id'];
        await _apiService.setToken(token, userId: userId);

        // Set current tenant as early as possible for faster availability
        final dynamic tn = (result['tenant_name'] ?? result['tenant'] ?? result['tenantName']);
        if (tn is String && tn.isNotEmpty) {
          _apiService.setCurrentTenantName(tn);
        } else {
          // Fallback: fetch users and infer tenant
          try {
            final users = await _apiService.getUsers();
            if (users.isNotEmpty) {
              _apiService.setCurrentTenantName(users.first.tenantName);
            }
          } catch (e) {
            // Non-fatal: proceed without tenant set, will be set later in dashboard
            print('Unable to set tenant at login (OTP): $e');
          }
        }

        if (mounted) {
          Navigator.pushReplacementNamed(context, '/home');
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to verify OTP: $e'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } finally {
        if (mounted) {
          setState(() {
            _isVerifyingOtp = false;
          });
        }
      }
    }
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _identifierController.dispose();
    _otpCodeController.dispose();
    _resendTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 60),
              Center(
                child: Container(
                  width: 150,
                  height: 150,
                  decoration: BoxDecoration(
                    color: Colors.transparent,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(20),
                    child: Image.asset(
                      'assets/Logo.png',
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) => Container(
                        width: 150,
                        height: 150,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(
                            colors: [Color(0xff0077B6), Color(0xff0096C7)],
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                          ),
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: const Icon(
                          Icons.chat_bubble_outline,
                          color: Colors.white,
                          size: 60,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 40),
              const Center(
                child: Text(
                  'Welcome Back',
                  style: TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1F2937),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              const Center(
                child: Text(
                  'Sign in to continue collaborating with your team',
                  style: TextStyle(
                    fontSize: 16,
                    color: Color(0xFF6B7280),
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 50),
              Form(
                key: _formKey,
                child: Column(
                  children: [
                    if (!_useOtpLogin) ...[
                      _buildInputField(
                        controller: _emailController,
                        label: 'Email or Phone',
                        hint: 'Enter your email or phone number',
                        icon: CupertinoIcons.person,
                        keyboardType: TextInputType.emailAddress,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter your email or phone';
                          }
                          final v = value.trim();
                          if (v.contains('@')) {
                            // Basic email format check
                            if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(v)) {
                              return 'Please enter a valid email';
                            }
                          } else {
                            // Basic phone check: at least 7 digits
                            final digits = v.replaceAll(RegExp(r'[^0-9]'), '');
                            if (digits.length < 7) {
                              return 'Please enter a valid phone number';
                            }
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 20),
                      _buildInputField(
                        controller: _passwordController,
                        label: 'Password',
                        hint: 'Enter your password',
                        icon: CupertinoIcons.lock,
                        obscureText: _obscurePassword,
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscurePassword ? CupertinoIcons.eye : CupertinoIcons.eye_slash,
                            color: const Color(0xFF6B7280),
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter your password';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 12),
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton(
                          onPressed: () => Navigator.pushNamed(context, '/forgot-password'),
                          child: const Text(
                            'Forgot Password?',
                            style: TextStyle(
                              color: Color(0xff0096C7), // Secondary blue for links
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: TextButton(
                          onPressed: () {
                            setState(() {
                              _useOtpLogin = true;
                            });
                          },
                          child: const Text(
                            'Use OTP instead',
                            style: TextStyle(
                              color: Color(0xff0096C7), // Secondary blue for OTP link
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _login,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xff0077B6), // Primary mid blue for main button
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: _isLoading
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                  ),
                                )
                              : const Text(
                                  'Sign In',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                        ),
                      ),
                    ] else ...[
                      _buildInputField(
                        controller: _identifierController,
                        label: 'Phone Number',
                        hint: 'Enter your phone number',
                        icon: CupertinoIcons.phone,
                        keyboardType: TextInputType.phone,
                        validator: (value) {
                          if (!_useOtpLogin) return null;
                          if (value == null || value.isEmpty) {
                            return 'Please enter your phone number';
                          }
                          if (value.contains('@')) {
                            return 'Please enter a valid phone number';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 20),
                      _buildInputField(
                        controller: _otpCodeController,
                        label: 'OTP Code',
                        hint: 'Enter the 6-digit code',
                        icon: CupertinoIcons.number,
                        keyboardType: TextInputType.number,
                        validator: (value) {
                          if (!_useOtpLogin) return null;
                          if (value == null || value.isEmpty) {
                            return 'Please enter the code';
                          }
                          if (value.length < 4) {
                            return 'Code seems too short';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 12),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          TextButton(
                            onPressed: (_isRequestingOtp || _retryAfter > 0)
                                ? null
                                : () async {
                                    await _requestOtpLogin();
                                  },
                            child: Text(
                              _retryAfter > 0 ? 'Resend in $_retryAfter s' : 'Request Code',
                              style: const TextStyle(color: Color(0xff0096C7)), // Secondary blue for resend text
                            ),
                          ),
                          TextButton(
                            onPressed: () {
                              setState(() {
                                _useOtpLogin = false;
                              });
                            },
                            child: const Text(
                              'Use password instead',
                              style: TextStyle(color: Color(0xFF6B7280)),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20),
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isVerifyingOtp ? null : _verifyOtpLogin,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xff0077B6), // Primary mid blue for verify button
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: _isVerifyingOtp
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                  ),
                                )
                              : const Text(
                                  'Verify & Sign In',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 32),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text(
                          'Don\'t have an account? ',
                          style: TextStyle(
                            color: Color(0xFF6B7280),
                            fontSize: 16,
                          ),
                        ),
                        TextButton(
                          onPressed: () => Navigator.pushNamed(context, '/signup'),
                          child: const Text(
                            'Sign Up',
                            style: TextStyle(
                              color: Color(0xff0096C7), // Secondary blue for sign up text
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInputField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    TextInputType? keyboardType,
    bool obscureText = false,
    Widget? suffixIcon,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: Color(0xFF1F2937),
          ),
        ),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: TextFormField(
            controller: controller,
            keyboardType: keyboardType,
            obscureText: obscureText,
            validator: validator,
            decoration: InputDecoration(
              hintText: hint,
              hintStyle: const TextStyle(
                color: Color(0xFF9CA3AF),
                fontSize: 16,
              ),
              prefixIcon: Icon(
                icon,
                color: const Color(0xFF6B7280),
                size: 20,
              ),
              suffixIcon: suffixIcon,
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 16,
              ),
            ),
          ),
        ),
      ],
    );
  }
}
