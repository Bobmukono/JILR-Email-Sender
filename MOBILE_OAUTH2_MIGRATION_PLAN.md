# Mobile App Migration Plan (OAuth2 + Gmail API)

## Goal
Migrate the desktop SMTP-based app to a mobile-ready architecture using Gmail OAuth2 and Gmail API.

## Recommended Architecture
- Mobile client: Flutter
- Backend API: FastAPI (Python)
- Auth model: Backend-managed Google OAuth2
- Storage: SQLite for MVP, upgradeable to Postgres

## Why This Architecture
- Better security: Gmail refresh tokens are kept on backend, not mobile devices.
- Better reliability: backend handles sending actions with stable API endpoints.
- Multi-user support: each user connects their own Gmail account.

## Phase 1: Contracts and Extraction
1. Define API contracts for auth, send, stats, and logs.
2. Extract business rules from desktop app:
   - interval variance
   - daily caps
   - operating-hour windows
   - send/failure counters

## Phase 2: Backend Foundation
1. Implement OAuth2 consent + callback flow.
2. Store refresh tokens per user securely.
3. Send mail using Gmail API users.messages.send.
4. Add single-send and batch-send endpoints.
5. Add persistence for users, jobs, and events.

## Phase 3: Mobile Client
1. Build Flutter screens:
   - connect Gmail
   - dashboard/stats
   - send single
   - send batch
2. Integrate with backend APIs.

## Scope Decision
- Continuous mode is excluded from mobile scope.
- Mobile supports manual single-send and batch-send only.

## Phase 4: Validation
1. Behavior parity checks against desktop app.
2. Multi-user isolation tests.
3. Token refresh and recovery tests.

## Phase 5: Release Hardening
1. Idempotency keys and rate protections.
2. Audit logs and operational alerts.
3. Deployment docs and rollback plan.

## Initial Implementation in This Repo
- New backend scaffold under mobile_backend/
- OAuth2 and Gmail API sending endpoints
- Local token store and event logging for MVP
