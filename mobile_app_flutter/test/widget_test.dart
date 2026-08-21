// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:jilr_mobile_sender/app.dart';
import 'package:jilr_mobile_sender/screens/send_email_screen.dart';

void main() {
  testWidgets('app renders home screen', (WidgetTester tester) async {
    await tester.pumpWidget(const JilrMobileApp());

    expect(find.text('JILR Mobile Sender'), findsOneWidget);
    expect(find.text('Login'), findsOneWidget);
  });

  testWidgets('send screen shows stop batch button while batch is running', (WidgetTester tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SendEmailScreen(
            recipientController: TextEditingController(),
            subjectController: TextEditingController(),
            bodyController: TextEditingController(),
            batchCountController: TextEditingController(),
            minDelayController: TextEditingController(),
            maxDelayController: TextEditingController(),
            busy: true,
            batchInProgress: true,
            status: 'Batch in progress',
            stats: null,
            selectedPlan: 'daily',
            onSendSingle: () async {},
            onSendBatch: () async {},
            onStopBatch: () async {},
            onRefreshStats: () async {},
            onResetStats: () async {},
          ),
        ),
      ),
    );

    expect(find.text('Stop Batch'), findsOneWidget);
  });
}
