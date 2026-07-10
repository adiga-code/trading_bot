"""Автовыдача VIP-доступа.

После оплаты: создаём/продлеваем подписку, генерируем одноразовую invite-ссылку
в VIP-канал и отправляем её пользователю. Фоновый цикл раз в час напоминает о
скором окончании и удаляет из канала тех, у кого подписка истекла.
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
    """Выдать/продлить VIP: подписка в БД + одноразовый инвайт в канал + is_vip=True."""
    settings = get_settings()
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

    invite_link = None
    if settings.vip_channel_id:
        try:
            invite = await bot.create_chat_invite_link(
                chat_id=settings.vip_channel_id,
                member_limit=1,
                name=f"vip {user_id}",
            )
            invite_link = invite.invite_link
            sub.invite_link = invite_link
        except Exception as exc:
            logger.error("create_chat_invite_link for %s: %s", user_id, exc)

    await repo.set_vip(session, user_id, True)
    await session.commit()

    # сообщение пользователю
    if expires_at:
        until = f"до <b>{expires_at:%d.%m.%Y}</b>"
    else:
        until = "<b>навсегда</b>"
    text = f"🎉 <b>Ваш VIP доступ активирован</b> 💎\n\nПодписка действует {until}."
    if invite_link:
        text += f"\n\n👉 Ссылка для входа в VIP-канал (одноразовая):\n{invite_link}"
    else:
        text += "\n\nАдминистратор пришлёт данные доступа в ближайшее время."
    try:
        await bot.send_message(user_id, text, parse_mode="HTML")
    except Exception as exc:
        logger.warning("grant_vip notify %s: %s", user_id, exc)

    return sub


async def revoke_vip(bot: Bot, session, sub: Subscription, *, notify: bool = True) -> None:
    """Пометить подписку истёкшей и убрать пользователя из VIP-канала."""
    settings = get_settings()
    await repo.expire_subscription(session, sub)

    if settings.vip_channel_id:
        try:
            # ban+unban = кик без перманентного бана: сможет вернуться по новой ссылке
            await bot.ban_chat_member(settings.vip_channel_id, sub.user_id)
            await bot.unban_chat_member(settings.vip_channel_id, sub.user_id)
        except Exception as exc:
            logger.warning("kick %s from vip channel: %s", sub.user_id, exc)

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


async def _tick(bot: Bot) -> None:
    settings = get_settings()
    remind_delta = timedelta(days=settings.subscription_remind_before_days)
    now = utcnow()

    async with get_sessionmaker()() as session:
        for sub in await repo.active_subscriptions(session):
            if sub.expires_at is None:
                continue
            if sub.expires_at <= now:
                logger.info("subscription %s of user %s expired", sub.id, sub.user_id)
                await revoke_vip(bot, session, sub)
            elif not sub.reminder_sent and sub.expires_at - now <= remind_delta:
                sub.reminder_sent = True
                await session.commit()
                try:
                    days_left = max(1, (sub.expires_at - now).days)
                    await bot.send_message(
                        sub.user_id,
                        f"⏳ Ваша VIP-подписка закончится через <b>{days_left} дн.</b>\n\n"
                        "Продлите заранее, чтобы не потерять доступ к сигналам.",
                        parse_mode="HTML",
                    )
                except Exception:
                    pass


async def scheduler_loop(bot: Bot) -> None:
    """Фоновая задача: запускается из lifespan приложения."""
    interval = get_settings().subscription_check_interval
    while True:
        try:
            await _tick(bot)
        except Exception as exc:
            logger.exception("subscription scheduler: %s", exc)
        await asyncio.sleep(interval)
