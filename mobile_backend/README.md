# Mobile Backend (FastAPI + Gmail OAuth2)

This backend is the first implementation step toward a mobile app migration.
It replaces SMTP auth with OAuth2 and sends email via Gmail API.

## Features
- Google OAuth2 connect flow per user
- Gmail API send single email endpoint
- Gmail API send batch endpoint
- Safaricom Daraja STK push subscription endpoints
- Local SQLite token and event store for MVP

## Quick Start
1. Create virtual environment and install dependencies.
2. Copy .env.example to .env and fill Google OAuth values.
3. Run API server.

## Setup
### 1) Install dependencies

```powershell
cd mobile_backend
pip install -r requirements.txt
```

### 2) Configure environment

```powershell
copy .env.example .env
```

Required values in .env:
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- GOOGLE_REDIRECT_URI
- DARAJA_CONSUMER_KEY
- DARAJA_CONSUMER_SECRET
- DARAJA_SHORTCODE
- DARAJA_PASSKEY
- DARAJA_CALLBACK_URL

Set OAuth redirect URI in Google Cloud Console to exactly match GOOGLE_REDIRECT_URI.
For Daraja, use `DARAJA_ENV=sandbox` for testing and `DARAJA_ENV=production` for live.

### 3) Start server

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

## API Flow
1. Mobile app calls GET /auth/start?user_id=someone@gmail.com
2. App opens returned authorization_url in browser
3. Google redirects to /auth/callback
4. Backend stores refresh token for user
5. App can now call POST /send/single or POST /send/batch

## Endpoints
- GET /health
- GET /auth/start?user_id=
- GET /auth/callback?state=&code=
- POST /auth/disconnect?user_id=
- POST /subscription/start
- GET /subscription/status?checkout_request_id=
- POST /send/single
- POST /send/batch
- POST /send/stop?user_id=
- GET /stats?user_id=

## Notes
- This is MVP storage. For production use encrypted token-at-rest and a managed database.
- Batch endpoint currently runs synchronously. Move to a worker queue for large volumes.
- Continuous mode is intentionally not part of mobile scope in this project.
