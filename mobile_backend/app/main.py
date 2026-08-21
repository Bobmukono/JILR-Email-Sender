import random
import time
from datetime import datetime
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow

from .config import load_settings
from .daraja_service import plan_amount, query_stk_status, start_stk_push
from .gmail_service import GMAIL_SCOPES, build_credentials, credentials_to_dict, send_message
from .schemas import (
    BatchResponse,
    SendBatchRequest,
    SendResponse,
    SendSingleRequest,
    SubscriptionStartRequest,
    SubscriptionStartResponse,
    SubscriptionStatusResponse,
    SubscriptionVerificationResponse,
)
from .token_store import TokenStore


settings = load_settings()
store = TokenStore(settings["token_db_path"])

app = FastAPI(title="JILR Mobile Backend", version="0.1.0")

# In-memory state tracker for OAuth callback verification.
pending_oauth_states: dict[str, str] = {}
batch_stop_requests: dict[str, bool] = {}


def _validate_oauth_config() -> None:
    if not settings["google_client_id"] or not settings["google_client_secret"]:
        raise HTTPException(status_code=500, detail="Google OAuth credentials are not configured")


def _build_flow(state: str | None = None) -> Flow:
    _validate_oauth_config()
    client_config = {
        "web": {
            "client_id": settings["google_client_id"],
            "client_secret": settings["google_client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = Flow.from_client_config(client_config, scopes=GMAIL_SCOPES, state=state)
    flow.redirect_uri = settings["google_redirect_uri"]
    return flow


def _get_user_credentials(user_id: str):
    token_data = store.get_token(user_id)
    if not token_data:
        raise HTTPException(status_code=404, detail="User is not connected to Gmail")

    creds = build_credentials(token_data, settings["google_client_id"], settings["google_client_secret"])
    store.save_token(user_id, credentials_to_dict(creds))
    return creds


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "mobile-backend"}


@app.get("/auth/start")
def auth_start(user_id: str = Query(..., min_length=1)) -> dict:
    flow = _build_flow()
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    pending_oauth_states[state] = user_id
    return {"authorization_url": authorization_url, "state": state}


@app.get("/auth/callback")
def auth_callback(state: str, code: str):
    user_id = pending_oauth_states.pop(state, None)
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    flow = _build_flow(state=state)
    flow.fetch_token(code=code)
    creds = flow.credentials
    store.save_token(user_id, credentials_to_dict(creds))

    app_redirect = settings["app_redirect_uri"]
    if app_redirect:
        query = urlencode({"status": "connected", "user_id": user_id})
        return RedirectResponse(url=f"{app_redirect}?{query}")

    return {"status": "connected", "user_id": user_id}


@app.post("/auth/disconnect")
def auth_disconnect(user_id: str = Query(..., min_length=1)) -> dict:
    store.delete_token(user_id)
    return {"status": "disconnected", "user_id": user_id}


@app.get("/auth/status")
def auth_status(user_id: str = Query(..., min_length=1)) -> dict:
    token_data = store.get_token(user_id)
    return {
        "user_id": user_id,
        "connected": token_data is not None,
    }


@app.post("/subscription/start", response_model=SubscriptionStartResponse)
def subscription_start(payload: SubscriptionStartRequest):
    return start_stk_push(
        settings=settings,
        user_id=payload.user_id,
        plan=payload.plan,
        phone_number=payload.phone_number,
    )


@app.get("/subscription/status", response_model=SubscriptionStatusResponse)
def subscription_status(checkout_request_id: str = Query(..., min_length=1)):
    return query_stk_status(settings=settings, checkout_request_id=checkout_request_id)


@app.get("/subscription/verify", response_model=SubscriptionVerificationResponse)
def subscription_verify(
    user_id: str = Query(..., min_length=1),
    checkout_request_id: str | None = None,
    plan: str | None = None,
):
    existing = store.get_subscription(user_id)
    if existing and existing.get("status") == "active":
        if store.has_active_subscription(user_id):
            return SubscriptionVerificationResponse(
                has_active_subscription=True,
                message="Active subscription found. You can continue to send emails.",
                plan=str(existing.get("plan", "")),
                checkout_request_id=str(existing.get("checkout_request_id", "")),
                status="active",
                expires_at=existing.get("expires_at"),
                amount=int(existing.get("amount", 0)),
            )
        store.mark_subscription_status(user_id, "expired")

    if not checkout_request_id:
        return SubscriptionVerificationResponse(
            has_active_subscription=False,
            message="You have not subscribed to any bundle yet. Complete a plan payment first."
            if not existing
            else "Your subscription has expired. Choose a plan to renew.",
            plan=plan,
            checkout_request_id=checkout_request_id,
            status="inactive",
        )

    # Prevent a stale checkout_request_id from an already-expired subscription from
    # silently re-activating it without a new M-Pesa payment.
    if existing and checkout_request_id == existing.get("checkout_request_id"):
        return SubscriptionVerificationResponse(
            has_active_subscription=False,
            message="Your subscription has expired. Please make a new payment to renew.",
            plan=plan,
            checkout_request_id=checkout_request_id,
            status="inactive",
        )

    status_payload = query_stk_status(settings=settings, checkout_request_id=checkout_request_id)
    if status_payload.get("status") == "success":
        amount = plan_amount(plan) if plan else 0
        store.save_subscription(
            user_id=user_id,
            plan=plan or "",
            amount=amount,
            checkout_request_id=checkout_request_id,
            status="active",
        )
        refreshed = store.get_subscription(user_id)
        return SubscriptionVerificationResponse(
            has_active_subscription=True,
            message="Payment confirmed. Your subscription is now active.",
            plan=plan,
            checkout_request_id=checkout_request_id,
            status="active",
            expires_at=refreshed.get("expires_at") if refreshed else None,
            amount=refreshed.get("amount") if refreshed else amount,
        )

    if status_payload.get("status") == "pending":
        store.mark_subscription_status(user_id, "pending")
        return SubscriptionVerificationResponse(
            has_active_subscription=False,
            message="Payment is still pending. Complete the M-Pesa prompt and try again.",
            plan=plan,
            checkout_request_id=checkout_request_id,
            status="pending",
        )

    store.mark_subscription_status(user_id, "inactive")
    return SubscriptionVerificationResponse(
        has_active_subscription=False,
        message="You have not subscribed to any bundle yet. Complete a plan payment first.",
        plan=plan,
        checkout_request_id=checkout_request_id,
        status="inactive",
    )


@app.post("/send/stop")
def stop_batch(user_id: str = Query(..., min_length=1)) -> dict:
    batch_stop_requests[user_id] = True
    return {"status": "stopping", "user_id": user_id}


@app.post("/send/single", response_model=SendResponse)
def send_single(payload: SendSingleRequest):
    today = datetime.utcnow().date().isoformat()
    sent_today = store.daily_sent_count(payload.user_id, today)
    if sent_today >= settings["max_daily_send"]:
        raise HTTPException(status_code=429, detail="Daily send limit reached")

    creds = _get_user_credentials(payload.user_id)

    try:
        send_message(
            creds=creds,
            sender=payload.user_id,
            recipient=payload.recipient,
            subject=payload.subject,
            body=payload.body,
        )
        store.log_event(payload.user_id, payload.recipient, payload.subject, True)
        return SendResponse(sent=True, message="Email sent")
    except Exception as exc:
        store.log_event(payload.user_id, payload.recipient, payload.subject, False, str(exc))
        raise HTTPException(status_code=500, detail=f"Gmail API send failed: {exc}")


@app.post("/send/batch", response_model=BatchResponse)
def send_batch(payload: SendBatchRequest):
    if payload.max_delay_seconds < payload.min_delay_seconds:
        raise HTTPException(status_code=400, detail="max_delay_seconds must be >= min_delay_seconds")

    creds = _get_user_credentials(payload.user_id)

    batch_stop_requests[payload.user_id] = False
    sent = 0
    failed = 0

    for index in range(payload.count):
        if batch_stop_requests.get(payload.user_id, False):
            break

        today = datetime.utcnow().date().isoformat()
        sent_today = store.daily_sent_count(payload.user_id, today)
        if sent_today >= settings["max_daily_send"]:
            break

        try:
            send_message(
                creds=creds,
                sender=payload.user_id,
                recipient=payload.recipient,
                subject=payload.subject,
                body=payload.body,
            )
            store.log_event(payload.user_id, payload.recipient, payload.subject, True)
            sent += 1
        except Exception as exc:
            store.log_event(payload.user_id, payload.recipient, payload.subject, False, str(exc))
            failed += 1

        if index < payload.count - 1:
            delay = random.uniform(payload.min_delay_seconds, payload.max_delay_seconds)
            time.sleep(delay)

    batch_stop_requests.pop(payload.user_id, None)
    return BatchResponse(requested=payload.count, sent=sent, failed=failed)


@app.get("/stats")
def get_stats(user_id: str = Query(..., min_length=1)) -> dict:
    today = datetime.utcnow().date().isoformat()
    stats = store.aggregate_stats(user_id, today)
    stats["daily_limit"] = settings["max_daily_send"]
    return stats


@app.post("/stats/reset")
def reset_stats(user_id: str = Query(..., min_length=1)) -> dict:
    store.reset_stats(user_id)
    return {"status": "reset", "user_id": user_id}
