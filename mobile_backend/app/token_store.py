import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

_PLAN_DURATION_DAYS = {
    "daily": 1,
    "weekly": 7,
    "fortnight": 14,
    "monthly": 30,
}


class TokenStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self) -> None:
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS gmail_tokens (
                    user_id TEXT PRIMARY KEY,
                    token_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS send_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    user_id TEXT PRIMARY KEY,
                    plan TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    checkout_request_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    expires_at TEXT
                )
                """
            )
            existing_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(subscriptions)").fetchall()
            }
            if "expires_at" not in existing_columns:
                conn.execute("ALTER TABLE subscriptions ADD COLUMN expires_at TEXT")

    def save_token(self, user_id: str, token_dict: dict) -> None:
        now = datetime.utcnow().isoformat()
        token_json = json.dumps(token_dict)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO gmail_tokens (user_id, token_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET token_json=excluded.token_json, updated_at=excluded.updated_at
                """,
                (user_id, token_json, now),
            )

    def get_token(self, user_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT token_json FROM gmail_tokens WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def delete_token(self, user_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM gmail_tokens WHERE user_id = ?", (user_id,))

    def save_subscription(
        self,
        user_id: str,
        plan: str,
        amount: int,
        checkout_request_id: str,
        status: str,
        expires_at: str | None = None,
    ) -> None:
        now = datetime.utcnow().isoformat()
        if status == "active" and expires_at is None:
            duration_days = _PLAN_DURATION_DAYS.get(plan.strip().lower(), 1)
            expires_at = (datetime.utcnow() + timedelta(days=duration_days)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO subscriptions (user_id, plan, amount, checkout_request_id, status, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET plan=excluded.plan, amount=excluded.amount, checkout_request_id=excluded.checkout_request_id, status=excluded.status, updated_at=excluded.updated_at, expires_at=excluded.expires_at
                """,
                (user_id, plan, amount, checkout_request_id, status, now, expires_at),
            )

    def get_subscription(self, user_id: str) -> dict | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT plan, amount, checkout_request_id, status, updated_at, expires_at FROM subscriptions WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "plan": row[0],
            "amount": int(row[1]),
            "checkout_request_id": row[2],
            "status": row[3],
            "updated_at": row[4],
            "expires_at": row[5],
        }

    def has_active_subscription(self, user_id: str) -> bool:
        subscription = self.get_subscription(user_id)
        if subscription is None or subscription.get("status") != "active":
            return False
        return not self._is_expired(subscription)

    def _is_expired(self, subscription: dict) -> bool:
        expires_at = subscription.get("expires_at")
        if not expires_at:
            # Legacy rows saved before expiry tracking existed have no expires_at;
            # backfill using updated_at + plan duration instead of treating them as never-expiring.
            updated_at = subscription.get("updated_at")
            if not updated_at:
                return False
            try:
                duration_days = _PLAN_DURATION_DAYS.get(str(subscription.get("plan", "")).strip().lower(), 1)
                expires_at = (datetime.fromisoformat(updated_at) + timedelta(days=duration_days)).isoformat()
            except ValueError:
                return False
        try:
            return datetime.utcnow() >= datetime.fromisoformat(expires_at)
        except ValueError:
            return False

    def mark_subscription_status(self, user_id: str, status: str) -> None:
        existing = self.get_subscription(user_id)
        if not existing:
            return
        self.save_subscription(
            user_id=user_id,
            plan=str(existing.get("plan", "")),
            amount=int(existing.get("amount", 0)),
            checkout_request_id=str(existing.get("checkout_request_id", "")),
            status=status,
            expires_at=existing.get("expires_at") if status == "active" else None,
        )

    def log_event(self, user_id: str, recipient: str, subject: str, success: bool, error_message: str = "") -> None:
        now = datetime.utcnow().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO send_events (user_id, recipient, subject, success, created_at, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, recipient, subject, 1 if success else 0, now, error_message),
            )

    def daily_sent_count(self, user_id: str, iso_date: str) -> int:
        date_prefix = f"{iso_date}%"
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) FROM send_events
                WHERE user_id = ? AND success = 1 AND created_at LIKE ?
                """,
                (user_id, date_prefix),
            ).fetchone()
        return int(row[0]) if row else 0

    def aggregate_stats(self, user_id: str, iso_date: str) -> dict:
        date_prefix = f"{iso_date}%"
        with sqlite3.connect(self.db_path) as conn:
            total_sent_row = conn.execute(
                "SELECT COUNT(*) FROM send_events WHERE user_id = ? AND success = 1",
                (user_id,),
            ).fetchone()
            failed_row = conn.execute(
                "SELECT COUNT(*) FROM send_events WHERE user_id = ? AND success = 0",
                (user_id,),
            ).fetchone()
            sent_today_row = conn.execute(
                """
                SELECT COUNT(*) FROM send_events
                WHERE user_id = ? AND success = 1 AND created_at LIKE ?
                """,
                (user_id, date_prefix),
            ).fetchone()

        return {
            "emails_sent_total": int(total_sent_row[0]) if total_sent_row else 0,
            "failed_emails": int(failed_row[0]) if failed_row else 0,
            "emails_sent_today": int(sent_today_row[0]) if sent_today_row else 0,
        }

    def reset_stats(self, user_id: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM send_events WHERE user_id = ?", (user_id,))
