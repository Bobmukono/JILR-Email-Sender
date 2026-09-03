import base64
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import gmail_service


def test_credentials_round_trip_preserves_expiry_for_refresh():
    creds = gmail_service.Credentials(
        token="access-token",
        refresh_token="refresh-token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client-id",
        client_secret="client-secret",
        scopes=gmail_service.GMAIL_SCOPES,
        expiry=datetime.utcnow() + timedelta(minutes=5),
    )

    payload = gmail_service.credentials_to_dict(creds)

    assert "expiry" in payload
    restored = gmail_service.build_credentials(payload, "client-id", "client-secret")
    assert restored.refresh_token == "refresh-token"
    assert restored.expiry is not None


def test_send_message_uses_authenticated_account_sender(monkeypatch):
    captured = {}

    class FakeMessages:
        def send(self, userId, body):
            captured["userId"] = userId
            captured["raw"] = body["raw"]
            return self

        def execute(self):
            return {"id": "msg-123"}

    class FakeService:
        def users(self):
            return self

        def messages(self):
            return FakeMessages()

    monkeypatch.setattr(gmail_service, "build", lambda *args, **kwargs: FakeService())

    gmail_service.send_message(
        creds=object(),
        sender="wrong-email@example.com",
        recipient="to@example.com",
        subject="Hello",
        body="Test body",
    )

    decoded = base64.urlsafe_b64decode(captured["raw"]).decode("utf-8")
    assert "From:" not in decoded
    assert "to: to@example.com" in decoded
    assert "subject: Hello" in decoded
    assert captured["userId"] == "me"
