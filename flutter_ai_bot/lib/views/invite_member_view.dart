import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter_ai_bot/network/api_service.dart';
import 'package:url_launcher/url_launcher.dart';

class InviteMemberView extends StatefulWidget {
  final ApiService apiService;
  final String fixedTenantName;

  const InviteMemberView({super.key, required this.apiService, required this.fixedTenantName});

  @override
  State<InviteMemberView> createState() => _InviteMemberViewState();
}

class _InviteMemberViewState extends State<InviteMemberView> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _fullNameController = TextEditingController();
  bool _isLoading = false;
  String _selectedRole = 'user';

  @override
  void dispose() {
    _emailController.dispose();
    _phoneController.dispose();
    _fullNameController.dispose();
    super.dispose();
  }

  Future<void> _launchSmsComposer(String phoneNumber, String message) async {
    final Uri smsLaunchUri = Uri(
      scheme: 'sms',
      path: phoneNumber,
      queryParameters: {'body': message},
    );

    if (await canLaunchUrl(smsLaunchUri)) {
      await launchUrl(smsLaunchUri);
    } else {
      throw 'Could not launch SMS composer for $phoneNumber';
    }
  }

  Future<void> _invite() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    try {
      final result = await widget.apiService.inviteMember(
        tenantName: widget.fixedTenantName,
        fullName: _fullNameController.text.trim(),
        phoneNumber: _phoneController.text.trim(),
        email: _emailController.text.trim().isEmpty ? null : _emailController.text.trim(),
        role: _selectedRole,
      );
      
      if (!mounted) return;
      
      // Show success dialog with temporary password
      showDialog(
        context: context,
        barrierDismissible: false,
        builder: (context) => AlertDialog(
          title: const Text('Member Invited Successfully'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${_fullNameController.text} has been invited to ${widget.fixedTenantName}.'),
              const SizedBox(height: 16),
              const Text('Temporary Password:', style: TextStyle(fontWeight: FontWeight.bold)),
              SelectableText(
                result['temporary_password'] ?? 'N/A',
                style: const TextStyle(fontFamily: 'monospace', fontSize: 16),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: () async {
                  try {
                    await _launchSmsComposer(
                      result['phone_number'] ?? _phoneController.text.trim(),
                      result['sms_message'] ?? 'Welcome message'
                    );
                  } catch (e) {
                    if (mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Could not open SMS: $e')),
                      );
                    }
                  }
                },
                icon: const Icon(Icons.sms),
                label: const Text('Send SMS'),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green,
                  foregroundColor: Colors.white,
                ),
              ),
              const SizedBox(height: 8),
              const Text('Tap "Send SMS" to open your SMS app with the login instructions.'),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.of(context).pop(); // Close dialog
                Navigator.pop(context, true); // Go back to previous screen
              },
              child: const Text('OK'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Failed to invite member: $e'),
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        backgroundColor: const Color(0xff023E8A), // Primary deep blue for app bar
        elevation: 0,
        leading: IconButton(
          icon: const Icon(CupertinoIcons.back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Invite Member',
          style: TextStyle(
            color: Colors.white,
            fontSize: 20,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: false,
        actions: [
          TextButton(
            onPressed: _isLoading ? null : _invite,
            child: Text(
              'Invite',
              style: TextStyle(
                color: _isLoading ? Colors.white54 : Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const SizedBox(height: 20),
              Center(
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    color: const Color(0xff48CAE4).withOpacity(0.2), // Soft blue background
                    borderRadius: BorderRadius.circular(40),
                  ),
                  child: const Icon(
                    CupertinoIcons.person_add,
                    color: Color(0xff48CAE4), // Soft blue for icon
                    size: 40,
                  ),
                ),
              ),
              const SizedBox(height: 24),
              const Center(
                child: Text(
                  'Add a Team Member',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1F2937),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Center(
                child: Text(
                  'Create account and send SMS with temporary password',
                  style: const TextStyle(
                    fontSize: 14,
                    color: Color(0xFF6B7280),
                  ),
                  textAlign: TextAlign.center,
                ),
              ),
              const SizedBox(height: 24),

              // Fixed tenant display card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
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
                child: Row(
                  children: [
                    const Icon(CupertinoIcons.building_2_fill, color: Color(0xFF6B7280), size: 20),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Organization',
                            style: TextStyle(
                              fontSize: 12,
                              color: Color(0xFF6B7280),
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            widget.fixedTenantName,
                            style: const TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFF1F2937),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 8),
                    const Icon(CupertinoIcons.lock_fill, size: 16, color: Color(0xFF9CA3AF)),
                  ],
                ),
              ),

              const SizedBox(height: 24),
              _buildInputField(
                controller: _fullNameController,
                label: 'Full Name',
                hint: 'Enter full name',
                icon: CupertinoIcons.person,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter full name';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              _buildInputField(
                controller: _phoneController,
                label: 'Phone Number',
                hint: 'Enter phone number (e.g., 9885794107)',
                icon: CupertinoIcons.phone,
                keyboardType: TextInputType.phone,
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter phone number';
                  }
                  final phoneRe = RegExp(r'^[\+]?[1-9]+[0-9]{7,15}$');
                  if (!phoneRe.hasMatch(value.trim().replaceAll(' ', ''))) {
                    return 'Please enter a valid phone number';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),
              _buildInputField(
                controller: _emailController,
                label: 'Email Address (Optional)',
                hint: 'Enter email (optional)',
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
              _buildRoleSelector(),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _invite,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xff0077B6), // Primary mid blue for button
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
                          'Create Account & Send SMS',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
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

  Widget _buildRoleSelector() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Role',
          style: TextStyle(
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
          child: DropdownButtonFormField<String>(
            value: _selectedRole,
            decoration: const InputDecoration(
              prefixIcon: Icon(
                CupertinoIcons.person_badge_plus,
                color: Color(0xFF6B7280),
                size: 20,
              ),
              border: InputBorder.none,
              contentPadding: EdgeInsets.symmetric(
                horizontal: 16,
                vertical: 16,
              ),
            ),
            items: const [
              DropdownMenuItem(value: 'user', child: Text('User')),
              DropdownMenuItem(value: 'admin', child: Text('Admin')),
              DropdownMenuItem(value: 'super_user', child: Text('Super User')),
            ],
            onChanged: (value) {
              setState(() {
                _selectedRole = value!;
              });
            },
          ),
        ),
      ],
    );
  }
}
