import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';

class ResetPasswordView extends StatefulWidget {
  final ApiService apiService;
  final String? initialToken;
  const ResetPasswordView({super.key, required this.apiService, this.initialToken});

  @override
  State<ResetPasswordView> createState() => _ResetPasswordViewState();
}

class _ResetPasswordViewState extends State<ResetPasswordView> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _tokenController;
  final _newController = TextEditingController();
  final _confirmController = TextEditingController();

  bool _isSubmitting = false;
  bool _obscureNew = true;
  bool _obscureConfirm = true;

  @override
  void initState() {
    super.initState();
    _tokenController = TextEditingController(text: widget.initialToken ?? '');
  }

  @override
  void dispose() {
    _tokenController.dispose();
    _newController.dispose();
    _confirmController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isSubmitting = true);
    try {
      await widget.apiService.resetPassword(
        token: _tokenController.text.trim(),
        newPassword: _newController.text,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Password has been reset. Please log in.'),
          backgroundColor: Color(0xff00B4D8), // Bright accent for success notifications
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
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Reset Password'),
        backgroundColor: const Color(0xff023E8A), // Primary deep blue for app bar
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Enter the reset token from your email and set a new password.',
                style: TextStyle(color: Color(0xFF6B7280)),
              ),
              const SizedBox(height: 16),
              _buildTokenField(),
              const SizedBox(height: 16),
              _buildPasswordField(
                label: 'New Password',
                controller: _newController,
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
                controller: _confirmController,
                obscure: _obscureConfirm,
                onToggle: () => setState(() => _obscureConfirm = !_obscureConfirm),
                validator: (v) {
                  if (v == null || v.isEmpty) return 'Confirm your new password';
                  if (v != _newController.text) return 'Passwords do not match';
                  return null;
                },
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: _isSubmitting ? null : _submit,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xff0077B6), // Primary mid blue for button
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: _isSubmitting
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
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTokenField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Reset Token',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Color(0xFF1F2937)),
        ),
        const SizedBox(height: 8),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            boxShadow: [
              BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, 2)),
            ],
          ),
          child: TextFormField(
            controller: _tokenController,
            validator: (v) => (v == null || v.trim().isEmpty) ? 'Enter your reset token' : null,
            decoration: const InputDecoration(
              hintText: 'Paste token here',
              hintStyle: TextStyle(color: Color(0xFF9CA3AF), fontSize: 16),
              prefixIcon: Icon(CupertinoIcons.tag, color: Color(0xFF6B7280), size: 20),
              border: InputBorder.none,
              contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPasswordField({
    required String label,
    required TextEditingController controller,
    required bool obscure,
    required VoidCallback onToggle,
    String? Function(String?)? validator,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: Color(0xFF1F2937)),
        ),
        const SizedBox(height: 8),
        Container(
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
        ),
      ],
    );
  }
}
