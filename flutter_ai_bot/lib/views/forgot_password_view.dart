import 'package:flutter/material.dart';
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
  final _emailController = TextEditingController();
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _apiService = widget.apiService;
  }

  void _sendResetLink() async {
    if (_formKey.currentState!.validate()) {
      setState(() {
        _isLoading = true;
      });

      try {
        await _apiService.forgotPassword(_emailController.text);
        // TODO: Show success message
        print('Password reset link sent');
      } catch (e) {
        // TODO: Show error message
        print('Failed to send reset link: $e');
      } finally {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Forgot Password')),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            children: [
              TextFormField(
                controller: _emailController,
                decoration: InputDecoration(labelText: 'Email'),
                validator: (value) {
                  if (value == null || value.isEmpty) {
                    return 'Please enter your email';
                  }
                  return null;
                },
              ),
              SizedBox(height: 20),
              _isLoading
                  ? CircularProgressIndicator()
                  : ElevatedButton(
                      onPressed: _sendResetLink,
                      child: Text('Send Reset Link'),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}
