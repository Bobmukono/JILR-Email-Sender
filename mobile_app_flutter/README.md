# JILR Mobile App (Flutter)

Flutter mobile client for the FastAPI OAuth2/Gmail backend in ../mobile_backend.

## Features (MVP)
- Connect Gmail account via backend OAuth2 flow
- Select a subscription plan and pay via M-Pesa STK Push (Daraja)
- Send single email
- Send batch emails
- View send statistics

## Setup
1. Install Flutter SDK.
2. Start backend API in ../mobile_backend.
3. In this folder, run:

```powershell
flutter pub get
flutter run
```

## Backend URL
The app now supports low-risk environment configuration at build time:

- APP_ENV: development | staging | production
- APP_BACKEND_URL: explicit backend URL override
- APP_ALLOW_BACKEND_OVERRIDE: true | false (show manual backend field in Login)
- APP_AUTH_MODE: legacy | firebase
- APP_FIREBASE_API_KEY, APP_FIREBASE_APP_ID, APP_FIREBASE_MESSAGING_SENDER_ID, APP_FIREBASE_PROJECT_ID
- Optional Firebase extras: APP_FIREBASE_AUTH_DOMAIN, APP_FIREBASE_STORAGE_BUCKET, APP_FIREBASE_MEASUREMENT_ID, APP_FIREBASE_ANDROID_CLIENT_ID, APP_FIREBASE_IOS_BUNDLE_ID

Defaults:

- Development: platform local backend (Android emulator uses http://10.0.2.2:8080)
- Staging: https://staging-api.jilr.app
- Production: https://api.jilr.app

The app also persists login identity preferences locally:

- Last used Gmail User ID is restored on next launch.
- Manual backend URL is restored when backend override is enabled.

Examples:

```powershell
flutter run --dart-define=APP_ENV=development
flutter run --dart-define=APP_ENV=staging
flutter run --dart-define=APP_BACKEND_URL=https://your-api.example.com
flutter run --dart-define=APP_ENV=production --dart-define=APP_ALLOW_BACKEND_OVERRIDE=true
flutter run --dart-define=APP_AUTH_MODE=firebase
```

To start the Firebase preview path on Android, supply the Firebase project values at launch:

```powershell
flutter run -d android ^
	--dart-define=APP_AUTH_MODE=firebase ^
	--dart-define=APP_FIREBASE_API_KEY=... ^
	--dart-define=APP_FIREBASE_APP_ID=... ^
	--dart-define=APP_FIREBASE_MESSAGING_SENDER_ID=... ^
	--dart-define=APP_FIREBASE_PROJECT_ID=...
```

If any of those values are missing or invalid, the app logs the failure and falls back to legacy OAuth automatically.

Firebase auth mode is guarded:

- If Firebase config is missing or initialization/sign-in fails, the app automatically falls back to legacy OAuth.
- The current Firebase path uses anonymous sign-in as a preview migration step, while the existing Gmail/backend flow remains intact.

## Notes
- For iOS simulator or physical device, use your machine LAN IP instead of 10.0.2.2.
- OAuth flow opens in external browser.

## Firebase Android Setup
- See [ANDROID_FIREBASE_SETUP.md](ANDROID_FIREBASE_SETUP.md) for the Android Firebase checklist, launch flags, and fallback behavior.
