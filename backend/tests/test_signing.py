"""Подпись 2328.io должна байт-в-байт совпадать со старой реализацией."""
import json

from app.payments.gate2328 import sign_body


def test_sign_matches_reference():
    body = {
        "amount": "45.00",
        "currency": "USD",
        "order_id": "123_1700000000",
        "description": "VIP 1 Месяц — Forex Trd'K",
    }
    body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=True)
    # эталон посчитан алгоритмом из старого payment.py (_sign)
    assert sign_body("test_api_key", body_json) == (
        "a763b97c1139f8858626717ed481ad8d36741732e8b2dffc670651fcfdeea3b2"
    )
