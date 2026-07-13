"""Клиент NicePay: конвертация в рубли, статусы платежа, подпись вебхука."""
import pytest

from app.payments.base import GatewayError
from app.payments.nicepay import NicePay


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

    def post(self, url, json=None, timeout=None):
        self.last_body = json
        return _FakeResponse(self._payload)


@pytest.fixture
def nicepay_settings(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("NICEPAY_MERCHANT_ID", "657b475da365fbeb3e5cfaf6")
    monkeypatch.setenv("NICEPAY_SECRET_KEY", "igDNT-tMppx-heMLB-Xjuw5-HIrdF")
    monkeypatch.setenv("NICEPAY_USD_RUB_RATE", "95")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_create_invoice_converts_to_rub_kopecks_and_forces_sbp(nicepay_settings):
    session = _FakeSession({
        "status": "success",
        "data": {"payment_id": "GdW668-5bab17", "link": "https://nicepay.io/pay/GdW668-5bab17", "expired": 1702577504},
    })
    invoice = await NicePay(session).create_invoice(
        amount_usd=45.0, order_id="100_1", description="VIP 1 Месяц", customer="@buyer",
    )

    assert session.last_body["currency"] == "RUB"
    assert session.last_body["method"] == "sbp_rub"
    assert session.last_body["amount"] == round(45.0 * 95 * 100)
    assert invoice.external_id == "GdW668-5bab17"
    assert invoice.payer_currency == "RUB"
    assert invoice.pay_url == "https://nicepay.io/pay/GdW668-5bab17"


async def test_create_invoice_requires_configured_rate(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("NICEPAY_MERCHANT_ID", "m")
    monkeypatch.setenv("NICEPAY_SECRET_KEY", "s")
    monkeypatch.delenv("NICEPAY_USD_RUB_RATE", raising=False)
    get_settings.cache_clear()

    session = _FakeSession({"status": "success", "data": {}})
    with pytest.raises(GatewayError):
        await NicePay(session).create_invoice(
            amount_usd=45.0, order_id="100_1", description="VIP", customer="@buyer",
        )
    get_settings.cache_clear()


async def test_create_invoice_rejects_response_without_payment_id(nicepay_settings):
    session = _FakeSession({"status": "success", "data": {"link": "https://nicepay.io/pay/x"}})
    with pytest.raises(GatewayError):
        await NicePay(session).create_invoice(
            amount_usd=45.0, order_id="100_1", description="VIP", customer="@buyer",
        )


async def test_create_invoice_surfaces_gateway_error_message(nicepay_settings):
    session = _FakeSession({"status": "error", "data": {"message": "Insufficient method"}})
    with pytest.raises(GatewayError, match="Insufficient method"):
        await NicePay(session).create_invoice(
            amount_usd=45.0, order_id="100_1", description="VIP", customer="@buyer",
        )


async def test_get_status_returns_numeric_payment_status(nicepay_settings):
    session = _FakeSession({"status": "success", "data": {"status": 5}})
    status = await NicePay(session).get_status("GdW668-5bab17")
    assert status == 5


async def test_get_status_returns_none_on_request_error(nicepay_settings):
    session = _FakeSession({"status": "error", "data": {"message": "Not found"}})
    status = await NicePay(session).get_status("unknown")
    assert status is None


async def test_verify_webhook_matches_documented_algorithm(nicepay_settings):
    # эталон посчитан вручную по алгоритму из документации NicePay:
    # sha256(значения по алфавиту ключей + secret, через "{np}")
    params = {
        "result": "success",
        "payment_id": "bVz657-bd8755-040148-6c9b6c-e47dld",
        "merchant_id": "657b475da365fbeb3e5cfaf6",
        "order_id": "100423",
        "amount": "5670",
        "amount_currency": "RUB",
        "profit": "5370",
        "profit_currency": "RUB",
        "method": "sbp_rub",
        "hash": "89f7194ac7e87abbb3202147ccdd8b6277512fffbcf2f8fd1502035751cbc8a2",
    }
    assert NicePay(_FakeSession({})).verify_webhook(params) is True


async def test_verify_webhook_rejects_tampered_params(nicepay_settings):
    params = {
        "result": "success",
        "payment_id": "bVz657-bd8755-040148-6c9b6c-e47dld",
        "merchant_id": "657b475da365fbeb3e5cfaf6",
        "order_id": "100423",
        "amount": "999999",  # подделанная сумма
        "amount_currency": "RUB",
        "profit": "5370",
        "profit_currency": "RUB",
        "method": "sbp_rub",
        "hash": "89f7194ac7e87abbb3202147ccdd8b6277512fffbcf2f8fd1502035751cbc8a2",
    }
    assert NicePay(_FakeSession({})).verify_webhook(params) is False
