"""Сквозные сценарии: подтверждение оплаты, автовыдача и истечение подписки."""
from datetime import timedelta

import pytest

from app.db import repo
from app.db.models import PaymentStatus, PocketOrderStatus, SubscriptionStatus, utcnow
from app.services.fulfillment import confirm_payment
from app.services.subscriptions import grant_vip, revoke_vip


@pytest.fixture
def vip_channel(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("VIP_CHANNEL_ID", "-1001234567890")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def _make_user(db, uid=100):
    return await repo.upsert_user(db, uid, "buyer", "Buy", "Er")


async def test_confirm_vip_payment_grants_subscription(db, fake_bot, vip_channel):
    user = await _make_user(db)
    payment = await repo.create_payment(
        db, user_id=user.id, gateway="gate2328", external_id="uuid-1",
        product_type="vip", plan_key="1month", plan_name="VIP 1 Месяц", amount_usd=45.0,
    )

    await confirm_payment(fake_bot, db, payment)

    assert payment.status == PaymentStatus.PAID
    sub = await repo.active_subscription(db, user.id)
    assert sub is not None and sub.status == SubscriptionStatus.ACTIVE
    assert sub.expires_at is not None
    assert sub.invite_link == "https://t.me/+test_invite"
    assert (await repo.get_user(db, user.id)).is_vip
    # пользователь получил инвайт, админ (id=1) — уведомление
    assert any(chat == user.id and "t.me/+test_invite" in text for chat, text in fake_bot.messages)
    assert any(chat == 1 for chat, _ in fake_bot.messages)


async def test_confirm_payment_idempotent(db, fake_bot):
    user = await _make_user(db)
    payment = await repo.create_payment(
        db, user_id=user.id, gateway="cryptopay", external_id="7",
        product_type="vip", plan_key="lifetime", plan_name="VIP Навсегда", amount_usd=199.0,
    )
    await confirm_payment(fake_bot, db, payment)
    count_after_first = len(fake_bot.messages)
    await confirm_payment(fake_bot, db, payment)  # второй раз — no-op
    assert len(fake_bot.messages) == count_after_first

    sub = await repo.active_subscription(db, user.id)
    assert sub.expires_at is None  # lifetime


async def test_confirm_pocket_payment_creates_order(db, fake_bot):
    user = await _make_user(db)
    payment = await repo.create_payment(
        db, user_id=user.id, gateway="gate2328", external_id="uuid-2",
        product_type="pocket", plan_key="1", plan_name="PocketOption $120→$175", amount_usd=120.0,
    )
    await confirm_payment(fake_bot, db, payment)

    orders = await repo.list_pocket_orders(db, status=PocketOrderStatus.NEW)
    assert len(orders) == 1
    order, _ = orders[0]
    assert order.user_id == user.id and order.balance_usd == 175.0


async def test_extension_adds_to_existing_subscription(db, fake_bot):
    user = await _make_user(db)
    sub1 = await grant_vip(fake_bot, db, user.id, "1month")
    first_expiry = sub1.expires_at
    sub2 = await grant_vip(fake_bot, db, user.id, "3months")
    assert sub2.id == sub1.id  # продлеваем ту же подписку
    assert sub2.expires_at > first_expiry + timedelta(days=85)


async def test_revoke_kicks_and_marks_expired(db, fake_bot, vip_channel):
    user = await _make_user(db)
    sub = await grant_vip(fake_bot, db, user.id, "1month")
    await revoke_vip(fake_bot, db, sub)

    assert sub.status == SubscriptionStatus.EXPIRED
    assert not (await repo.get_user(db, user.id)).is_vip
    assert fake_bot.banned == [user.id] and fake_bot.unbanned == [user.id]


async def test_scheduler_tick_expires_overdue(db, fake_bot, vip_channel, monkeypatch):
    from app.services import subscriptions as subs_module

    user = await _make_user(db)
    sub = await grant_vip(fake_bot, db, user.id, "1month")
    sub.expires_at = utcnow() - timedelta(days=1)
    await db.commit()

    # _tick открывает собственную сессию — подменяем sessionmaker на тестовый
    from app.db.session import get_sessionmaker
    monkeypatch.setattr(subs_module, "get_sessionmaker", get_sessionmaker)
    await subs_module._tick(fake_bot)

    async with get_sessionmaker()() as check:
        assert (await repo.active_subscription(check, user.id)) is None
        assert not (await repo.get_user(check, user.id)).is_vip
