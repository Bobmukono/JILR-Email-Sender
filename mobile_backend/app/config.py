import os
from pathlib import Path
from dotenv import load_dotenv


def load_settings() -> dict:
    root_dir = Path(__file__).resolve().parents[1]
    env_path = root_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=True)

    token_db_path_raw = os.getenv("TOKEN_DB_PATH", "data/tokens.sqlite3")
    token_db_path = str((root_dir / token_db_path_raw).resolve())

    return {
        "api_host": os.getenv("API_HOST", "127.0.0.1"),
        "api_port": int(os.getenv("API_PORT", "8080")),
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID", "").strip(),
        "google_client_secret": os.getenv("GOOGLE_CLIENT_SECRET", "").strip(),
        "google_redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://127.0.0.1:8080/auth/callback").strip(),
        "app_redirect_uri": os.getenv("APP_REDIRECT_URI", "").strip(),
        "token_db_path": token_db_path,
        "max_daily_send": int(os.getenv("MAX_DAILY_SEND", "2000")),
        "daraja_env": os.getenv("DARAJA_ENV", "sandbox").strip().lower(),
        "daraja_consumer_key": os.getenv("DARAJA_CONSUMER_KEY", "").strip(),
        "daraja_consumer_secret": os.getenv("DARAJA_CONSUMER_SECRET", "").strip(),
        "daraja_shortcode": os.getenv("DARAJA_SHORTCODE", os.getenv("DARAJA_SHORT_CODE", "")).strip(),
        "daraja_passkey": os.getenv("DARAJA_PASSKEY", "").strip(),
        "daraja_callback_url": os.getenv("DARAJA_CALLBACK_URL", "").strip(),
    }
