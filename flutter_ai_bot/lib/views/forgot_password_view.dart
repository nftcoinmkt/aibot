import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import '../network/api_service.dart';

class ForgotPasswordView extends StatefulWidget {
  final ApiService apiService;

  const ForgotPasswordView({super.key, required this.apiService});

  @override
  _ForgotPasswordViewState createState() => _ForgotPasswordViewState();
}

class _ForgotPasswordViewState extends State<ForgotPasswordView> {
  late final ApiService _apiService;

  final _formKey = GlobalKey<FormState>();
  final _contactController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  bool _isLoading = false;
  bool _otpSent = false;
  bool _obscureNew = true;
  bool _obscureConfirm = true;
  String _contactType = 'email'; // 'email' or 'phone'

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService;
  }

  void _sendOtp() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        await _apiService.requestOtp(
          contactType: _contactType,
          contact: _contactController.text.trim(),
          purpose: 'reset_password',
        );
        if (!mounted) return;
        setState(() {
          _otpSent = true;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('OTP sent successfully. Please check your email/phone.'),
            backgroundColor: Color(0xFF25D366),
          ),
        );
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to send OTP: $e'),
            backgroundColor: Colors.red,
          ),
        );
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  void _resetPassword() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        await _apiService.resetPasswordWithOtp(
          contactType: _contactType,
          contact: _contactController.text.trim(),
          code: _otpController.text.trim(),
          newPassword: _newPasswordController.text,
        );
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Password reset successfully. Please login with your new password.'),
            backgroundColor: Color(0xFF25D366),
          ),
        );
        Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to reset password: $e'),
            backgroundColor: Colors.red,
          ),
        );
      } finally {
        if (mounted) {
          setState(() {
            _isLoading = false;
          });
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Reset Password'),
        backgroundColor: const Color(0xFF25D366),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!_otpSent) ..._buildContactForm() else ..._buildOtpForm(),
            ],
          ),
        ),
      ),
    );
  }

  List<Widget> _buildContactForm() {
    return [
      const Text(
        'Choose how you want to receive your reset code:',
        style: TextStyle(fontSize: 16, color: Color(0xFF6B7280)),
      ),
      const SizedBox(height: 16),
      Row(
        children: [
          Expanded(
            child: RadioListTile<String>(
              title: const Text('Email'),
              value: 'email',
              groupValue: _contactType,
              onChanged: (value) => setState(() => _contactType = value!),
              activeColor: const Color(0xFF25D366),
            ),
          ),
          Expanded(
            child: RadioListTile<String>(
              title: const Text('Phone'),
              value: 'phone',
              groupValue: _contactType,
              onChanged: (value) => setState(() => _contactType = value!),
              activeColor: const Color(0xFF25D366),
            ),
          ),
        ],
      ),
      const SizedBox(height: 16),
      _buildContactField(),
      const SizedBox(height: 24),
      SizedBox(
        width: double.infinity,
        height: 48,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ElevatedButton(
                onPressed: _sendOtp,
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF25D366),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text('Send Reset Code', style: TextStyle(fontWeight: FontWeight.w600)),
              ),
      ),
    ];
  }

  List<Widget> _buildOtpForm() {
    return [
      Text(
        'Enter the reset code sent to your ${_contactType}:',
        style: const TextStyle(fontSize: 16, color: Color(0xFF6B7280)),
      ),
      const SizedBox(height: 16),
      _buildOtpField(),
      const SizedBox(height: 16),
      _buildPasswordField(
        label: 'New Password',
        controller: _newPasswordController,
        obscure: _obscureNew,
        onToggle: () => setState(() => _obscureNew = !_obscureNew),
        validator: (v) {
          if (v == null || v.isEmpty) return 'Enter a new password';
          if (v.length < 8) return 'Password must be at least 8 characters';
          return null;
        },
      ),
      const SizedBox(height: 16),
      _buildPasswordField(
        label: 'Confirm New Password',
        controller: _confirmPasswordController,
        obscure: _obscureConfirm,
        onToggle: () => setState(() => _obscureConfirm = !_obscureConfirm),
        validator: (v) {
          if (v == null || v.isEmpty) return 'Confirm your new password';
          if (v != _newPasswordController.text) return 'Passwords do not match';
          return null;
        },
      ),
      const SizedBox(height: 24),
      SizedBox(
        width: double.infinity,
        height: 48,
        child: ElevatedButton(
          onPressed: _isLoading ? null : _resetPassword,
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF25D366),
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
              : const Text('Reset Password', style: TextStyle(fontWeight: FontWeight.w600)),
        ),
      ),
      const SizedBox(height: 16),
      TextButton(
        onPressed: () => setState(() => _otpSent = false),
        child: const Text(
          'Back to contact selection',
          style: TextStyle(color: Color(0xFF25D366), fontWeight: FontWeight.w500),
        ),
      ),
    ];
  }

  Widget _buildContactField() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 2)),
        ],
      ),
      child: TextFormField(
        controller: _contactController,
        keyboardType: _contactType == 'email' ? TextInputType.emailAddress : TextInputType.phone,
        decoration: InputDecoration(
          hintText: _contactType == 'email' ? 'Enter your email' : 'Enter your phone number',
          hintStyle: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 16),
          prefixIcon: Icon(
            _contactType == 'email' ? CupertinoIcons.mail : CupertinoIcons.phone,
            color: const Color(0xFF6B7280),
            size: 20,
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        validator: (value) {
          if (value == null || value.isEmpty) {
            return 'Please enter your ${_contactType}';
          }
          if (_contactType == 'email') {
            final emailRe = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
            if (!emailRe.hasMatch(value.trim())) {
              return 'Please enter a valid email';
            }
          } else {
            final phoneRe = RegExp(r'^[\+]?[1-9]+[0-9]{7,15}$');
            if (!phoneRe.hasMatch(value.trim().replaceAll(' ', ''))) {
              return 'Please enter a valid phone number';
            }
          }
          return null;
        },
      ),
    );
  }

  Widget _buildOtpField() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 2)),
        ],
      ),
      child: TextFormField(
        controller: _otpController,
        keyboardType: TextInputType.number,
        decoration: const InputDecoration(
          hintText: 'Enter 6-digit code',
          hintStyle: TextStyle(color: Color(0xFF9CA3AF), fontSize: 16),
          prefixIcon: Icon(CupertinoIcons.number, color: Color(0xFF6B7280), size: 20),
          border: InputBorder.none,
          contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
        validator: (v) => (v == null || v.trim().length != 6) ? 'Enter 6-digit code' : null,
      ),
    );
  }

  Widget _buildPasswordField({
    required String label,
    required TextEditingController controller,
    required bool obscure,
    required VoidCallback onToggle,
    String? Function(String?)? validator,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 2)),
        ],
      ),
      child: TextFormField(
        controller: controller,
        obscureText: obscure,
        validator: validator,
        decoration: InputDecoration(
          hintText: label,
          hintStyle: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 16),
          prefixIcon: const Icon(CupertinoIcons.lock, color: Color(0xFF6B7280), size: 20),
          suffixIcon: IconButton(
            icon: Icon(obscure ? CupertinoIcons.eye : CupertinoIcons.eye_slash, color: const Color(0xFF6B7280)),
            onPressed: onToggle,
          ),
          border: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        ),
      ),
    );
  }
}
