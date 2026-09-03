# Android Firebase Setup Checklist

Use this checklist to prepare the Firebase preview path for the Flutter Android app.

## 1. Create the Firebase project
- Open the Firebase Console.
- Create or select the project for JILR EMAIL Sender.
- Enable Authentication.
- Enable the sign-in methods you need for the migration path.

## 2. Register the Android app
- Add an Android app in Firebase.
- Use the app package name: `com.jilr.emailsender`.
- Download the generated `google-services.json` file.

## 3. Place the Firebase config file
- Copy `google-services.json` into:
  - `mobile_app_flutter/android/app/google-services.json`
- Do not commit any private Firebase secrets unless you intentionally want them in source control.

## 4. Collect the launch values
Use these Firebase values with `--dart-define`:

- `APP_FIREBASE_API_KEY`
- `APP_FIREBASE_APP_ID`
- `APP_FIREBASE_MESSAGING_SENDER_ID`
- `APP_FIREBASE_PROJECT_ID`
- Optional:
  - `APP_FIREBASE_AUTH_DOMAIN`
  - `APP_FIREBASE_STORAGE_BUCKET`
  - `APP_FIREBASE_MEASUREMENT_ID`
  - `APP_FIREBASE_ANDROID_CLIENT_ID`
  - `APP_FIREBASE_IOS_BUNDLE_ID`

## 5. Run the app in Firebase mode
Example Android launch command:

```powershell
flutter run -d android `
  --dart-define=APP_AUTH_MODE=firebase `
  --dart-define=APP_FIREBASE_API_KEY="AIza...REDACTED" `
  --dart-define=APP_FIREBASE_APP_ID="1:716341702547:android:f2c87d2284c16ec7a78266" `
  --dart-define=APP_FIREBASE_MESSAGING_SENDER_ID="716341702547" `
  --dart-define=APP_FIREBASE_PROJECT_ID="jilr-email-sender-9074e" `
  --dart-define=APP_FIREBASE_STORAGE_BUCKET="jilr-email-sender-9074e.firebasestorage.app" `
  --dart-define=APP_FIREBASE_AUTH_DOMAIN="jilr-email-sender-9074e.firebaseapp.com"
```

## 6. Confirm fallback behavior
- If Firebase config is missing, the app should fall back to legacy OAuth.
- If Firebase initialization fails on device, the app should also fall back automatically.
- Keep the legacy backend login path working until Firebase is fully proven.

## 7. Recommended migration order
- Android first.
- Verify Firebase startup and auth preview on Android.
- Keep the legacy Gmail/backend flow available as fallback.
- Only after Android is stable, mirror the same approach for Windows or other targets.
