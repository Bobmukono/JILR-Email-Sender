import base64
import json
from datetime import datetime
from email.mime.text import MIMEText

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailReauthRequired(Exception):
    """Refresh token was rejected by Google (revoked/expired); user must reconnect."""


def build_credentials(token_data: dict, client_id: str, client_secret: str) -> Credentials:
    expiry_value = token_data.get("expiry")
    expiry = None
    if expiry_value:
        if isinstance(expiry_value, str):
            expiry_text = expiry_value.replace("Z", "+00:00")
            try:
                expiry = datetime.fromisoformat(expiry_text)
            except ValueError:
                expiry = None
        else:
            expiry = expiry_value

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=client_id,
        client_secret=client_secret,
        scopes=token_data.get("scopes", GMAIL_SCOPES),
        expiry=expiry,
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except RefreshError as exc:
            raise GmailReauthRequired(
                "Gmail authorization expired or was revoked. Reconnect your Gmail account."
            ) from exc

    return creds


def credentials_to_dict(creds: Credentials) -> dict:
    expiry = getattr(creds, "expiry", None)
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": expiry.isoformat() if expiry else None,
    }


def _extract_gmail_error(exc: Exception) -> str:
    if not isinstance(exc, HttpError):
        return str(exc)

    try:
        payload = json.loads(exc.content.decode("utf-8", errors="ignore") or "{}")
    except (AttributeError, TypeError, ValueError):
        return str(exc)

    error_info = payload.get("error", {}) if isinstance(payload, dict) else {}
    if isinstance(error_info, dict):
        message = error_info.get("message")
        if message:
            return str(message)
    return str(exc)


def send_message(creds: Credentials, sender: str, recipient: str, subject: str, body: str) -> str:
    if not recipient or "@" not in recipient:
        raise ValueError("recipient is invalid")
    if not subject.strip():
        raise ValueError("subject is required")
    if not body.strip():
        raise ValueError("body is required")

    message = MIMEText(body, _charset="utf-8")
    message["to"] = recipient
    message["subject"] = subject

    # Gmail API sends from the authenticated account when userId="me". Setting a
    # custom From header to the app's user_id can be rejected if it does not match
    # the connected account or is not a verified alias.
    if sender and "@" in sender and sender.lower().endswith("@gmail.com"):
        message["from"] = sender

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    try:
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    except HttpError as exc:
        raise RuntimeError(f"Gmail API send failed: {_extract_gmail_error(exc)}") from exc

    return result.get("id", "")
