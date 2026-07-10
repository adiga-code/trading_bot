"""Учёт VIP-подписок.

После оплаты подписка фиксируется в БД, пользователь получает подтверждение,
а доступ в VIP-канал выдаёт админ вручную. Фоновый цикл раз в час уведомляет
админов о подписках, которые скоро закончатся или уже истекли.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiogram import Bot

from app.config import get_settings
from app.db import repo
from app.db.models import Subscription, SubscriptionStatus, utcnow
from app.db.session import get_sessionmaker
from app.plans import VIP_PLANS

logger = logging.getLogger(__name__)


async def notify_admins(bot: Bot, text: str, reply_markup=None) -> None:
    for admin_id in get_settings().admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception as exc:
            logger.warning("notify admin %s: %s", admin_id, exc)


async def grant_vip(bot: Bot, session, user_id: int, plan_key: str) -> Subscription:
    """Выдать/продлить VIP: подписка в БД + is_vip=True. Доступ в канал выдаёт админ."""
    plan = VIP_PLANS.get(plan_key)
    months = plan.months if plan else None

    sub = await repo.active_subscription(session, user_id)
    now = utcnow()
    if months is None:
        expires_at = None
    else:
        # продление отсчитываем от конца текущей подписки, если она ещё активна
        base = sub.expires_at if sub and sub.expires_at and sub.expires_at > now else now
        expires_at = base + timedelta(days=30 * months)

    if sub:
        sub.plan_key = plan_key
        sub.expires_at = expires_at
        sub.reminder_sent = False
    else:
        sub = Subscription(user_id=user_id, plan_key=plan_key, expires_at=expires_at)
        session.add(sub)

    await repo.set_vip(session, user_id, True)
    await session.commit()

    # сообщение пользователю
    if expires_at:
        until = f"до <b>{expires_at:%d.%m.%Y}</b>"
    else:
        until = "<b>навсегда</b>"
    text = (
        f"🎉 <b>Ваш VIP доступ активирован</b> 💎\n\nПодписка действует {until}.\n\n"
        "Администратор пришлёт ссылку на VIP-канал в ближайшее время."
    )
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("grant_vip notify %s: %s", user_id, exc)

    return sub


async def revoke_vip(bot: Bot, session, sub: Subscription, *, notify: bool = True) -> None:
    """Пометить подписку истёкшей (из канала пользователя убирает админ вручную)."""
    await repo.expire_subscription(session, sub)

    if notify:
        try:
            await bot.send_message(
                sub.user_id,
                "⌛ <b>Ваша VIP-подписка закончилась.</b>\n\n"
                "Продлить можно в любой момент через меню бота или Mini App.",
                parse_mode="HTML",
            )
        except Exception:
            pass


def _who(user, user_id: int) -> str:
    if user:
        uname = f" (@{user.username})" if user.username else ""
        return f"{user.display_name}{uname}"
    return f"ID:{user_id}"


async def _tick(bot: Bot) -> None:
    settings = get_settings()
    remind_delta = timedelta(days=settings.subscription_remind_before_days)
    now = utcnow()

    async with get_sessionmaker()() as session:
        for sub in await repo.active_subscriptions(session):
            if sub.expires_at is None:
                continue
            user = await repo.get_user(session, sub.user_id)
            who = _who(user, sub.user_id)
            if sub.expires_at <= now:
                logger.info("subscription %s of user %s expired", sub.id, sub.user_id)
                await revoke_vip(bot, session, sub)
                await notify_admins(
                    bot,
                    f"⏰ <b>VIP-подписка истекла</b>\n\n"
                    f"👤 {who}\n🆔 <code>{sub.user_id}</code>\n"
                    f"📦 Тариф: {sub.plan_key}\n\n"
                    f"➡️ Убери пользователя из VIP-канала вручную.",
                )
            elif not sub.reminder_sent and sub.expires_at - now <= remind_delta:
                sub.reminder_sent = True
                await session.commit()
                days_left = max(1, (sub.expires_at - now).days)
                await notify_admins(
                    bot,
                    f"⏳ <b>VIP-подписка скоро закончится</b>\n\n"
                    f"👤 {who}\n🆔 <code>{sub.user_id}</code>\n"
                    f"📦 Тариф: {sub.plan_key}\n"
                    f"📅 Осталось: <b>{days_left} дн.</b> (до {sub.expires_at:%d.%m.%Y})",
                )


async def scheduler_loop(bot: Bot) -> None:
    """Фоновая задача: запускается из lifespan приложения."""
    interval = get_settings().subscription_check_interval
    while True:
        try:
            await _tick(bot)
        except Exception as exc:
            logger.exception("subscription scheduler: %s", exc)
        await asyncio.sleep(interval)
