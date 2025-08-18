// Flutter AI Bot widget tests

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:flutter_ai_bot/main.dart';

void main() {
  testWidgets('App loads and shows loading indicator', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const MyApp());

    // Verify that the app loads with a loading indicator initially
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    
    // Verify the app title is set correctly
    final MaterialApp app = tester.widget(find.byType(MaterialApp));
    expect(app.title, 'Flutter AI Bot');
  });

  testWidgets('App has correct theme colors', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    
    final MaterialApp app = tester.widget(find.byType(MaterialApp));
    expect(app.theme?.primaryColor, const Color(0xff075E54));
    expect(app.theme?.scaffoldBackgroundColor, const Color(0xffECE5DD));
  });
}
