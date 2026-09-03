import 'package:flutter_test/flutter_test.dart';

import 'package:jilr_mobile_sender/services/app_config.dart';

void main() {
  test('Android development builds use phone-reachable backend', () {
    final config = AppConfig.fromBuild();

    expect(config.backendBaseUrl, 'https://jilr-email-sender-1.onrender.com');
  });
}