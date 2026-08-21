import base64
from datetime import datetime

import requests
from fastapi import HTTPException


_PLAN_PRICES = {
    "daily": 10,
    "weekly": 40,
    "fortnight": 80,
    "monthly": 150,
}


def plan_amount(plan: str) -> int:
    key = plan.strip().lower()
    if key not in _PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Unsupported subscription plan")
    return _PLAN_PRICES[key]


def normalize_msisdn(phone_number: str) -> str:
    digits = "".join(ch for ch in phone_number if ch.isdigit())
    if digits.startswith("0") and len(digits) == 10:
        return f"254{digits[1:]}"
    if digits.startswith("254") and len(digits) == 12:
        return digits
    if digits.startswith("7") and len(digits) == 9:
        return f"254{digits}"
    raise HTTPException(status_code=400, detail="Phone number must be a valid Safaricom number")


def _daraja_base_url(env_name: str) -> str:
    if env_name == "production":
        return "https://api.safaricom.co.ke"
    return "https://sandbox.safaricom.co.ke"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S")


def _password(shortcode: str, passkey: str, timestamp: str) -> str:
    plain = f"{shortcode}{passkey}{timestamp}".encode("utf-8")
    return base64.b64encode(plain).decode("utf-8")


def _require_daraja_config(settings: dict) -> None:
    required = [
        "daraja_consumer_key",
        "daraja_consumer_secret",
        "daraja_shortcode",
        "daraja_passkey",
        "daraja_callback_url",
    ]
    missing = [key for key in required if not settings.get(key)]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing Daraja configuration: {', '.join(missing)}",
        )


def _access_token(settings: dict) -> str:
    _require_daraja_config(settings)
    base_url = _daraja_base_url(settings["daraja_env"])
    url = f"{base_url}/oauth/v1/generate?grant_type=client_credentials"

    try:
        response = requests.get(
            url,
            auth=(settings["daraja_consumer_key"], settings["daraja_consumer_secret"]),
            timeout=20,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach Daraja OAuth: {exc}") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Daraja OAuth failed: {response.text}")

    data = response.json()
    token = data.get("access_token")
    if not token:
        raise HTTPException(status_code=502, detail="Daraja OAuth response had no access_token")

    return token


def start_stk_push(*, settings: dict, user_id: str, plan: str, phone_number: str) -> dict:
    amount = plan_amount(plan)
    msisdn = normalize_msisdn(phone_number)
    token = _access_token(settings)

    timestamp = _timestamp()
    shortcode = settings["daraja_shortcode"]
    password = _password(shortcode, settings["daraja_passkey"], timestamp)
    base_url = _daraja_base_url(settings["daraja_env"])

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": msisdn,
        "PartyB": shortcode,
        "PhoneNumber": msisdn,
        "CallBackURL": settings["daraja_callback_url"],
        "AccountReference": user_id,
        "TransactionDesc": f"JILR {plan.title()} plan",
    }

    url = f"{base_url}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not start STK push: {exc}") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"STK push failed: {response.text}")

    data = response.json()
    if data.get("ResponseCode") != "0":
        raise HTTPException(status_code=400, detail=f"STK push rejected: {data}")

    return {
        "merchant_request_id": data.get("MerchantRequestID", ""),
        "checkout_request_id": data.get("CheckoutRequestID", ""),
        "response_code": data.get("ResponseCode", ""),
        "response_description": data.get("ResponseDescription", ""),
        "customer_message": data.get("CustomerMessage", ""),
        "amount": amount,
    }


def query_stk_status(*, settings: dict, checkout_request_id: str) -> dict:
    if not checkout_request_id.strip():
        raise HTTPException(status_code=400, detail="checkout_request_id is required")

    try:
        token = _access_token(settings)
    except HTTPException as exc:
        detail_text = str(exc.detail)
        if "Daraja OAuth failed" in detail_text or "Could not reach Daraja OAuth" in detail_text:
            return {
                "result_code": "",
                "result_desc": "Payment confirmation is temporarily unavailable. Please try again shortly.",
                "checkout_request_id": checkout_request_id,
                "status": "pending",
            }
        raise

    timestamp = _timestamp()
    shortcode = settings["daraja_shortcode"]
    password = _password(shortcode, settings["daraja_passkey"], timestamp)
    base_url = _daraja_base_url(settings["daraja_env"])

    payload = {
        "BusinessShortCode": shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id,
    }

    url = f"{base_url}/mpesa/stkpushquery/v1/query"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not query STK status: {exc}") from exc

    if response.status_code != 200:
        response_text = response.text or ""
        looks_like_html_error = "<html" in response_text.lower() or "incapsula" in response_text.lower()
        if looks_like_html_error:
            return {
                "result_code": "",
                "result_desc": "Payment confirmation is temporarily unavailable. Please try again shortly.",
                "checkout_request_id": checkout_request_id,
                "status": "pending",
            }
        raise HTTPException(status_code=502, detail=f"STK query failed: {response_text}")

    data = response.json()
    result_code = str(data.get("ResultCode", ""))
    status = "pending"
    if result_code == "0":
        status = "success"
    elif result_code:
        status = "failed"

    return {
        "result_code": result_code,
        "result_desc": data.get("ResultDesc", ""),
        "checkout_request_id": data.get("CheckoutRequestID", checkout_request_id),
        "status": status,
    }
