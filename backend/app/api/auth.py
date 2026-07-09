"""Проверка Telegram WebApp initData.

Каждый запрос из Mini App несёт заголовок `Authorization: tma <initData>`.
Подпись проверяется по алгоритму Telegram: secret = HMAC_SHA256("WebAppData", bot_token),
hash = HMAC_SHA256(secret, data_check_string). Без валидной подписи запрос отклоняется —
в старой версии API принимал user_id из тела запроса без всякой проверки.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl

from fastapi import Depends, Header, HTTPException

from app.config import get_settings

MAX_AGE_SECONDS = 24 * 3600


@dataclass
class WebAppUser:
    id: int
    username: str | None
    first_name: str | None
    last_name: str | None

    @property
    def is_admin(self) -> bool:
        return get_settings().is_admin(self.id)


def validate_init_data(init_data: str, bot_token: str, *, max_age: int = MAX_AGE_SECONDS) -> dict:
    """Разбирает и проверяет initData; возвращает поля или бросает ValueError."""
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception as exc:
        raise ValueError("bad init data") from exc

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise ValueError("hash missing")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, received_hash):
        raise ValueError("hash mismatch")

    auth_date = int(pairs.get("auth_date", "0") or 0)
    if max_age and auth_date and time.time() - auth_date > max_age:
        raise ValueError("init data expired")

    return pairs


def _auth_header_to_user(authorization: str | None) -> WebAppUser:
    if not authorization or not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    settings = get_settings()
    if not settings.bot_token:
        raise HTTPException(status_code=503, detail="Bot is not configured")
    try:
        fields = validate_init_data(authorization[4:], settings.bot_token)
        user = json.loads(fields.get("user", "{}"))
        user_id = int(user["id"])
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=401, detail="Invalid init data")
    return WebAppUser(
        id=user_id,
        username=user.get("username"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
    )


async def current_user(authorization: str | None = Header(default=None)) -> WebAppUser:
    return _auth_header_to_user(authorization)


async def current_admin(user: WebAppUser = Depends(current_user)) -> WebAppUser:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return user
