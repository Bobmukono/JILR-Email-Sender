// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:jilr_mobile_sender/app.dart';
import 'package:jilr_mobile_sender/screens/login_screen.dart';
import 'package:jilr_mobile_sender/screens/send_email_screen.dart';
import 'package:jilr_mobile_sender/screens/subscription_screen.dart';

void main() {
  testWidgets('app renders home screen', (WidgetTester tester) async {
    await tester.pumpWidget(const JilrMobileApp());

    expect(find.text('JILR Email Sender'), findsOneWidget);
    expect(find.text('Login'), findsOneWidget);
  });

  testWidgets('send screen shows stop batch button while batch is running',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(280, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

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
            activePlanName: 'daily',
            activePlanAmount: 10,
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
    expect(tester.takeException(), isNull);
  });

  testWidgets('login screen fits a narrow portrait phone',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(280, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: LoginScreen(
            baseUrlController: TextEditingController(),
            userIdController: TextEditingController(),
            showBackendUrlField: false,
            authModeLabel: 'legacy oauth',
            authModeNotice: 'Legacy backend OAuth mode is active.',
            busy: false,
            status: 'Ready',
            onConnectOAuth: () {},
            onDisconnectOAuth: () {},
            onContinue: () {},
            onEnableBackendOverride: () {},
            continueButtonLabel: 'Continue to Subscription',
          ),
        ),
      ),
    );

    expect(find.textContaining('Auth mode:'), findsNothing);
    expect(find.text('Server is configured automatically for this build.'),
        findsNothing);
    expect(find.text('Configure server manually'), findsNothing);
    expect(find.text('Disconnect'), findsNothing);
    expect(find.text('Need help with Google authentication?'), findsNothing);
    expect(tester.takeException(), isNull);
  });

  testWidgets('subscription screen fits a narrow portrait phone',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(280, 640);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: SubscriptionScreen(
            selectedPlan: 'monthly',
            phoneController: TextEditingController(),
            busy: false,
            status: 'Ready',
            paymentCompleted: false,
            hasPendingPayment: false,
            onPlanSelected: (_) {},
            onPay: () async {},
            onContinue: () {},
          ),
        ),
      ),
    );

    expect(tester.takeException(), isNull);
  });
}
