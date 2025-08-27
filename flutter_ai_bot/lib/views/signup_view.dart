import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import '../network/api_service.dart';
import 'dart:async';

class SignupView extends StatefulWidget {
  final ApiService apiService;

  const SignupView({super.key, required this.apiService});

  @override
  _SignupViewState createState() => _SignupViewState();
}

class _SignupViewState extends State<SignupView> {
  late final ApiService _apiService;
  final _formKey = GlobalKey<FormState>();
  
  // Form controllers
  final _phoneController = TextEditingController();
  final _emailController = TextEditingController();
  final _fullNameController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _otpController = TextEditingController();
  
  // UI state
  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _showOtpStep = false;
  
  // Organization/Tenant selection
  List<Map<String, dynamic>> _availableTenants = [];
  String? _selectedTenantId;
  bool _loadingTenants = true;
  
  // OTP state
  bool _isRequestingOtp = false;
  bool _isVerifyingOtp = false;
  int _retryAfter = 0;
  Timer? _resendTimer;
  int _otpExpirySeconds = 300; // 5 minutes default
  Timer? _expiryTimer;

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService;
    _loadAvailableTenants();
  }

  Future<void> _loadAvailableTenants() async {
    try {
      final tenants = await _apiService.getAvailableTenants();
      if (mounted) {
        setState(() {
          _availableTenants = tenants;
          _loadingTenants = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _loadingTenants = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to load organizations: $e'),
            backgroundColor: Colors.red,
          ),
        );
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

  void _startOtpExpiryTimer() {
    _expiryTimer?.cancel();
    setState(() {
      _otpExpirySeconds = 300; // 5 minutes
    });
    _expiryTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (!mounted) {
        timer.cancel();
        return;
      }
      if (_otpExpirySeconds <= 1) {
        setState(() {
          _otpExpirySeconds = 0;
          _showOtpStep = false; // Auto-hide OTP step when expired
        });
        timer.cancel();
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('OTP has expired. Please request a new code.'),
            backgroundColor: Colors.red,
          ),
        );
      } else {
        setState(() {
          _otpExpirySeconds -= 1;
        });
      }
    });
  }

  Future<void> _requestOtp() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedTenantId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select an organization first'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isRequestingOtp = true;
    });
    
    try {
      final phone = _phoneController.text.trim();
      final email = _emailController.text.trim();
      
      // Determine which contact method to use for OTP
      String contactType = 'phone';
      String contact = phone;
      
      // If email is provided and phone is empty, use email for OTP
      if (phone.isEmpty && email.isNotEmpty) {
        contactType = 'email';
        contact = email;
      }
      
      final resp = await _apiService.requestOtp(
        contactType: contactType,
        contact: contact,
        purpose: 'signup',
        tenantName: _selectedTenantId,
      );
      
      final bool sent = resp['sent'] == true;
      final int retry = (resp['retry_after'] ?? 30) as int;
      
      if (sent && mounted) {
        setState(() {
          _showOtpStep = true;
        });
        _startOtpExpiryTimer(); // Start expiry timer
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('OTP sent to your ${contactType == 'phone' ? 'phone' : 'email'}.'),
            backgroundColor: const Color(0xFF25D366),
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

  Future<void> _verifyOtpAndSignup() async {
    if (!_formKey.currentState!.validate()) return;
    if (_selectedTenantId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please select an organization'),
          backgroundColor: Colors.red,
        ),
      );
      return;
    }

    setState(() {
      _isVerifyingOtp = true;
    });

    try {
      final phone = _phoneController.text.trim();
      final email = _emailController.text.trim();
      final code = _otpController.text.trim();
      final fullName = _fullNameController.text.trim();
      final password = _passwordController.text.trim();
      final tenantName = _selectedTenantId!;
      
      // Determine which contact method was used for OTP
      String contactType = 'phone';
      String contact = phone;
      
      if (phone.isEmpty && email.isNotEmpty) {
        contactType = 'email';
        contact = email;
      }

      final result = await _apiService.verifySignupOtp(
        contactType: contactType,
        contact: contact,
        code: code,
        fullName: fullName,
        tenantName: tenantName,
        password: password,
        email: email.isNotEmpty ? email : null,
      );

      final String token = result['access_token'];
      final int userId = result['user_id'];
      await _apiService.setToken(token, userId: userId);

      final dynamic tn = (result['tenant_name'] ?? result['tenant'] ?? result['tenantName']);
      if (tn is String && tn.isNotEmpty) {
        _apiService.setCurrentTenantName(tn);
      }

      if (mounted) {
        Navigator.pushReplacementNamed(context, '/home');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Signup failed: $e'),
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


  @override
  void dispose() {
    _phoneController.dispose();
    _emailController.dispose();
    _fullNameController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _otpController.dispose();
    _resendTimer?.cancel();
    _expiryTimer?.cancel();
    super.dispose();
  }

  Widget _buildOrganizationDropdown() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Organization',
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w600,
            color: Color(0xFF374151),
          ),
        ),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: const Color(0xFFE5E7EB)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 10,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: _loadingTenants
              ? const Padding(
                  padding: EdgeInsets.all(16.0),
                  child: Row(
                    children: [
                      SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                      SizedBox(width: 12),
                      Text('Loading organizations...'),
                    ],
                  ),
                )
              : DropdownButtonFormField<String>(
                  value: _selectedTenantId,
                  decoration: const InputDecoration(
                    hintText: 'Select your organization',
                    prefixIcon: Icon(CupertinoIcons.building_2_fill, color: Color(0xFF6B7280)),
                    border: InputBorder.none,
                    contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
                  ),
                  items: _availableTenants.map((tenant) {
                    return DropdownMenuItem<String>(
                      value: tenant['id'],
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Text(
                            tenant['name'],
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 14,
                            ),
                          ),
                          if (tenant['description'] != null)
                            Text(
                              tenant['description'],
                              style: const TextStyle(
                                color: Color(0xFF6B7280),
                                fontSize: 12,
                              ),
                            ),
                        ],
                      ),
                    );
                  }).toList(),
                  onChanged: (value) {
                    setState(() {
                      _selectedTenantId = value;
                    });
                  },
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Please select an organization';
                    }
                    return null;
                  },
                ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFF25D366),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(CupertinoIcons.back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: Text(
          _showOtpStep ? 'Verify OTP' : 'Create Account',
          style: const TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: false,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              Center(
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: const Color(0xFF25D366).withOpacity(0.1),
                    borderRadius: BorderRadius.circular(40),
                  ),
                  child: Icon(
                    _showOtpStep ? CupertinoIcons.checkmark_shield : CupertinoIcons.person_add,
                    color: const Color(0xFF25D366),
                    size: 40,
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Center(
                child: Text(
                  _showOtpStep ? 'Verify Your Account' : 'Join Your Team',
                  style: const TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1F2937),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Center(
                child: Text(
                  _showOtpStep 
                    ? 'Enter the verification code sent to your phone or email'
                    : 'Create your account to start collaborating',
                  style: const TextStyle(
                    fontSize: 16,
                    color: Color(0xFF6B7280),
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 40),
              Form(
                key: _formKey,
                child: Column(
                  children: [
                    if (!_showOtpStep) ...[
                      // Step 1: Signup Form
                      _buildInputField(
                        controller: _phoneController,
                        label: 'Phone Number',
                        hint: 'Enter your phone number',
                        icon: CupertinoIcons.phone,
                        keyboardType: TextInputType.phone,
                        validator: (value) {
                          final phone = value?.trim() ?? '';
                          final email = _emailController.text.trim();
                          if (phone.isEmpty && email.isEmpty) {
                            return 'Please enter your phone number or email';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      _buildInputField(
                        controller: _emailController,
                        label: 'Email Address (Optional)',
                        hint: 'Enter your email (optional)',
                        icon: CupertinoIcons.mail,
                        keyboardType: TextInputType.emailAddress,
                        validator: (value) {
                          if (value != null && value.isNotEmpty) {
                            if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
                              return 'Please enter a valid email';
                            }
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      _buildInputField(
                        controller: _fullNameController,
                        label: 'Full Name',
                        hint: 'Enter your full name',
                        icon: CupertinoIcons.person,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter your full name';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      _buildInputField(
                        controller: _passwordController,
                        label: 'Password',
                        hint: 'Create a strong password',
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
                          if (value.length < 6) {
                            return 'Password must be at least 6 characters';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      _buildInputField(
                        controller: _confirmPasswordController,
                        label: 'Confirm Password',
                        hint: 'Confirm your password',
                        icon: CupertinoIcons.lock,
                        obscureText: _obscureConfirmPassword,
                        suffixIcon: IconButton(
                          icon: Icon(
                            _obscureConfirmPassword ? CupertinoIcons.eye : CupertinoIcons.eye_slash,
                            color: const Color(0xFF6B7280),
                          ),
                          onPressed: () {
                            setState(() {
                              _obscureConfirmPassword = !_obscureConfirmPassword;
                            });
                          },
                        ),
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please confirm your password';
                          }
                          if (value != _passwordController.text) {
                            return 'Passwords do not match';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      _buildOrganizationDropdown(),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isRequestingOtp ? null : _requestOtp,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF25D366),
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                          child: _isRequestingOtp
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                  ),
                                )
                              : const Text(
                                  'Sign Up',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                        ),
                      ),
                    ] else ...[
                      // Step 2: OTP Verification
                      _buildInputField(
                        controller: _otpController,
                        label: 'OTP Code',
                        hint: 'Enter the verification code',
                        icon: CupertinoIcons.number,
                        keyboardType: TextInputType.number,
                        validator: (value) {
                          if (value == null || value.isEmpty) {
                            return 'Please enter the verification code';
                          }
                          if (value.length < 4) {
                            return 'Code seems too short';
                          }
                          return null;
                        },
                      ),
                      const SizedBox(height: 16),
                      // OTP Expiry Timer
                      Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: _otpExpirySeconds <= 60 ? Colors.red.withOpacity(0.1) : const Color(0xFF25D366).withOpacity(0.1),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: _otpExpirySeconds <= 60 ? Colors.red.withOpacity(0.3) : const Color(0xFF25D366).withOpacity(0.3),
                          ),
                        ),
                        child: Row(
                          children: [
                            Icon(
                              CupertinoIcons.time,
                              color: _otpExpirySeconds <= 60 ? Colors.red : const Color(0xFF25D366),
                              size: 16,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Code expires in ${(_otpExpirySeconds / 60).floor()}:${(_otpExpirySeconds % 60).toString().padLeft(2, '0')}',
                              style: TextStyle(
                                color: _otpExpirySeconds <= 60 ? Colors.red : const Color(0xFF25D366),
                                fontWeight: FontWeight.w600,
                                fontSize: 14,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          TextButton(
                            onPressed: (_isRequestingOtp || _retryAfter > 0)
                                ? null
                                : () async {
                                    await _requestOtp();
                                  },
                            child: Text(
                              _retryAfter > 0 ? 'Resend in $_retryAfter s' : 'Resend Code',
                              style: const TextStyle(color: Color(0xFF25D366)),
                            ),
                          ),
                          TextButton(
                            onPressed: () {
                              setState(() {
                                _showOtpStep = false;
                                _otpController.clear();
                                _expiryTimer?.cancel();
                              });
                            },
                            child: const Text(
                              'Back to Form',
                              style: TextStyle(color: Color(0xFF6B7280)),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      SizedBox(
                        width: double.infinity,
                        height: 50,
                        child: ElevatedButton(
                          onPressed: _isVerifyingOtp ? null : _verifyOtpAndSignup,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF25D366),
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
                                  'Confirm Signup',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                        ),
                      ),
                    ],
                    const SizedBox(height: 24),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        const Text(
                          'Already have an account? ',
                          style: TextStyle(
                            color: Color(0xFF6B7280),
                            fontSize: 16,
                          ),
                        ),
                        TextButton(
                          onPressed: () {
                            Navigator.pushReplacementNamed(context, '/login');
                          },
                          child: const Text(
                            'Sign In',
                            style: TextStyle(
                              color: Color(0xFF25D366),
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
