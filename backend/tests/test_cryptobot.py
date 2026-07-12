"""Клиент CryptoBot: expires_in синхронизирован с TTL watcher'а, invoice_id обязателен."""
import pytest

from app.payments.base import GatewayError, PENDING_TTL_SECONDS
from app.payments.cryptobot import CryptoBot


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    async def json(self):
        return self._payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeSession:
    """Заглушка вместо aiohttp.ClientSession — фиксирует последний запрос и отдаёт canned-ответ."""

    def __init__(self, payload):
        self._payload = payload
        self.last_body: dict | None = None

    def post(self, url, json=None, headers=None, timeout=None):
        self.last_body = json
        return _FakeResponse(self._payload)


@pytest.fixture
def cryptobot_token(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("CRYPTOBOT_API_TOKEN", "test-token")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_create_invoice_sends_expires_in_matching_watcher_ttl(cryptobot_token):
    session = _FakeSession({
        "ok": True,
        "result": {"invoice_id": 42, "mini_app_invoice_url": "https://t.me/x", "amount": "45.00"},
    })
    invoice = await CryptoBot(session).create_invoice(amount_usd=45.0, order_id="1_100", description="VIP")

    assert session.last_body["expires_in"] == PENDING_TTL_SECONDS
    assert invoice.external_id == "42"


async def test_create_invoice_rejects_response_without_invoice_id(cryptobot_token):
    session = _FakeSession({"ok": True, "result": {"mini_app_invoice_url": "https://t.me/x"}})
    with pytest.raises(GatewayError):
        await CryptoBot(session).create_invoice(amount_usd=45.0, order_id="1_100", description="VIP")


async def test_create_invoice_accepts_invoice_id_zero(cryptobot_token):
    """invoice_id=0 не должен тихо подменяться на order_id (falsy-zero баг)."""
    session = _FakeSession({"ok": True, "result": {"invoice_id": 0, "pay_url": "https://t.me/x"}})
    invoice = await CryptoBot(session).create_invoice(amount_usd=45.0, order_id="1_100", description="VIP")

    assert invoice.external_id == "0"
