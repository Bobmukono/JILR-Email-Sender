import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.token_store import TokenStore


def test_subscription_state_is_persisted_and_checked(tmp_path):
    db_path = tmp_path / "tokens.sqlite3"
    store = TokenStore(str(db_path))

    store.save_subscription(
        user_id="user@example.com",
        plan="monthly",
        amount=150,
        checkout_request_id="checkout-123",
        status="active",
    )

    subscription = store.get_subscription("user@example.com")
    assert subscription is not None
    assert subscription["plan"] == "monthly"
    assert subscription["status"] == "active"
    assert store.has_active_subscription("user@example.com") is True

    store.mark_subscription_status("user@example.com", "inactive")
    assert store.has_active_subscription("user@example.com") is False


def test_active_subscription_expires_after_plan_duration(tmp_path):
    db_path = tmp_path / "tokens.sqlite3"
    store = TokenStore(str(db_path))

    store.save_subscription(
        user_id="user@example.com",
        plan="daily",
        amount=10,
        checkout_request_id="checkout-daily",
        status="active",
    )
    subscription = store.get_subscription("user@example.com")
    assert subscription["expires_at"] is not None
    assert store.has_active_subscription("user@example.com") is True

    # Simulate the daily plan having expired (more than 1 day old).
    past_expiry = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    store.save_subscription(
        user_id="user@example.com",
        plan="daily",
        amount=10,
        checkout_request_id="checkout-daily",
        status="active",
        expires_at=past_expiry,
    )

    assert store.has_active_subscription("user@example.com") is False


def test_different_plans_get_correct_expiry_duration(tmp_path):
    db_path = tmp_path / "tokens.sqlite3"
    store = TokenStore(str(db_path))
    expected_days = {"daily": 1, "weekly": 7, "fortnight": 14, "monthly": 30}

    for plan, days in expected_days.items():
        user_id = f"user-{plan}@example.com"
        store.save_subscription(
            user_id=user_id,
            plan=plan,
            amount=1,
            checkout_request_id=f"checkout-{plan}",
            status="active",
        )
        subscription = store.get_subscription(user_id)
        expires_at = datetime.fromisoformat(subscription["expires_at"])
        expected = datetime.utcnow() + timedelta(days=days)
        assert abs((expires_at - expected).total_seconds()) < 5

