"""Проверка валидации Telegram WebApp initData."""
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from app.api.auth import validate_init_data

TOKEN = "12345:TEST_TOKEN"


def make_init_data(user_id: int = 42, auth_date: int | None = None, token: str = TOKEN) -> str:
    fields = {
        "user": json.dumps({"id": user_id, "first_name": "Test", "username": "tester"}),
        "auth_date": str(auth_date if auth_date is not None else int(time.time())),
        "query_id": "AAF_test",
    }
    dcs = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, dcs.encode(), hashlib.sha256).hexdigest()
    return urlencode(fields)


def test_valid_init_data():
    fields = validate_init_data(make_init_data(), TOKEN)
    assert json.loads(fields["user"])["id"] == 42


def test_tampered_hash_rejected():
    data = make_init_data() + "x"
    with pytest.raises(ValueError):
        validate_init_data(data, TOKEN)


def test_wrong_token_rejected():
    data = make_init_data(token="999:OTHER")
    with pytest.raises(ValueError):
        validate_init_data(data, TOKEN)


def test_expired_rejected():
    data = make_init_data(auth_date=int(time.time()) - 100_000)
    with pytest.raises(ValueError):
        validate_init_data(data, TOKEN)


def test_missing_hash_rejected():
    with pytest.raises(ValueError):
        validate_init_data("user=%7B%7D&auth_date=1", TOKEN)
