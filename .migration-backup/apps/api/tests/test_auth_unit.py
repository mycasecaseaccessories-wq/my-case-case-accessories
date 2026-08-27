import hashlib
import hmac
import json
import time
from urllib.parse import urlencode
from uuid import uuid4

import pytest

from app.auth import User, _decode_token, _hash_password, _make_token, _validate_telegram_init_data, _verify_password


def test_password_hash_round_trip() -> None:
    encoded = _hash_password("correct-horse-battery")
    assert encoded != "correct-horse-battery"
    assert _verify_password("correct-horse-battery", encoded)
    assert not _verify_password("wrong-password", encoded)


def test_signed_token_round_trip() -> None:
    user = User(id=uuid4(), email="person@example.com", password_hash="unused", role="customer")
    token = _make_token(user)
    claims = _decode_token(token)
    assert claims["sub"] == str(user.id)
    assert claims["role"] == "customer"


def _telegram_init_data(bot_token: str) -> str:
    values = {"auth_date": str(int(time.time())), "query_id": "query-1", "user": json.dumps({"id": 123, "username": "customer"}, separators=(",", ":"))}
    check = "\n".join(f"{key}={values[key]}" for key in sorted(values))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    values["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return urlencode(values)


def test_telegram_init_data_signature_and_expiry() -> None:
    signed = _telegram_init_data("test-bot-token")
    assert _validate_telegram_init_data(signed, "test-bot-token")["auth_date"]
    with pytest.raises(ValueError):
        _validate_telegram_init_data(signed, "wrong-token")
