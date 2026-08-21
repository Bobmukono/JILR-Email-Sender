import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def build_credentials(token_data: dict, client_id: str, client_secret: str) -> Credentials:
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=client_id,
        client_secret=client_secret,
        scopes=token_data.get("scopes", GMAIL_SCOPES),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def credentials_to_dict(creds: Credentials) -> dict:
    return {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }


def send_message(creds: Credentials, sender: str, recipient: str, subject: str, body: str) -> str:
    message = MIMEText(body)
    message["to"] = recipient
    message["from"] = sender
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    service = build("gmail", "v1", credentials=creds)
    result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return result.get("id", "")
