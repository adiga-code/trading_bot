"""HTTP-уровень: авторизация initData обязательна, админ-роуты закрыты."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.test_initdata import make_init_data


@pytest.fixture
async def client(db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200 and r.json() == {"ok": True}


async def test_config_public(client):
    r = await client.get("/api/config")
    data = r.json()
    assert r.status_code == 200
    assert len(data["vip_plans"]) == 4
    assert len(data["pocket_tiers"]) == 3
    assert data["vip_plans"][0]["price_usd"] == 45.0


async def test_pay_requires_auth(client):
    r = await client.post("/api/pay", json={"type": "vip", "plan": "1month"})
    assert r.status_code == 401


async def test_pay_rejects_bad_initdata(client):
    r = await client.post(
        "/api/pay",
        json={"type": "vip", "plan": "1month"},
        headers={"Authorization": "tma user=fake&hash=deadbeef"},
    )
    assert r.status_code == 401


async def test_pay_cryptobot_requires_auth(client):
    r = await client.post("/api/pay/cryptobot", json={"type": "vip", "plan": "1month"})
    assert r.status_code == 401


async def test_pay_nicepay_requires_auth(client):
    r = await client.post("/api/pay/nicepay", json={"type": "vip", "plan": "1month"})
    assert r.status_code == 401


async def test_nicepay_webhook_rejects_bad_hash(client, db, monkeypatch):
    """Вебхук NicePay не требует initData — авторизация через подпись hash."""
    from app.config import get_settings
    monkeypatch.setenv("NICEPAY_SECRET_KEY", "test-secret")
    get_settings.cache_clear()

    from app.db import repo
    from app.db.models import PaymentStatus

    user = await repo.upsert_user(db, 100, "buyer", "Buy", "Er")
    payment = await repo.create_payment(
        db, user_id=user.id, gateway="nicepay", external_id="pay123",
        product_type="vip", plan_key="1month", plan_name="VIP 1 Месяц", amount_usd=45.0,
    )

    r = await client.get("/api/webhooks/nicepay", params={
        "result": "success", "payment_id": "pay123", "merchant_id": "m",
        "order_id": "1", "amount": "1", "amount_currency": "RUB",
        "profit": "1", "profit_currency": "RUB", "method": "sbp_rub",
        "hash": "deadbeef",
    })
    assert r.status_code == 200
    assert "error" in r.json()

    await db.refresh(payment)
    assert payment.status == PaymentStatus.PENDING
    get_settings.cache_clear()


async def test_admin_requires_admin_id(client):
    # валидный initData, но user_id=42 не входит в ADMIN_IDS=[1]
    r = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"tma {make_init_data(user_id=42)}"},
    )
    assert r.status_code == 403


async def test_admin_ok_for_admin(client):
    r = await client.get(
        "/api/admin/stats",
        headers={"Authorization": f"tma {make_init_data(user_id=1)}"},
    )
    assert r.status_code == 200
    assert r.json()["users"]["total"] == 0


async def test_me_upserts_user(client):
    r = await client.get("/api/me", headers={"Authorization": f"tma {make_init_data(user_id=42)}"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == 42 and body["is_admin"] is False
