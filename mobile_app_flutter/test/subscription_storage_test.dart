import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:path_provider_windows/path_provider_windows.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

import 'package:jilr_mobile_sender/services/subscription_storage.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
    PathProviderPlatform.instance = PathProviderWindows();
  });

  test('saves and recalls the selected plan, payment status, phone number and checkout request ID', () async {
    final storage = SubscriptionStorage.instance;
    await storage.clear();

    await storage.saveSelectedPlan('weekly');
    await storage.savePaymentCompleted(true);
    await storage.savePhoneNumber('0712345678');
    await storage.savePendingCheckoutRequestId('test-checkout-id');

    expect(await storage.loadSelectedPlan(defaultPlan: 'daily'), 'weekly');
    expect(await storage.loadPaymentCompleted(defaultValue: false), true);
    expect(await storage.loadPhoneNumber(defaultValue: ''), '0712345678');
    expect(await storage.loadPendingCheckoutRequestId(defaultValue: ''), 'test-checkout-id');
  });
}
