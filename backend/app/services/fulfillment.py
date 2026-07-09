"""Что происходит после подтверждения оплаты: покупка, выдача, уведомления."""
from __future__ import annotations

import logging

from aiogram import Bot

from app.config import get_settings
from app.db import repo
from app.db.models import Payment, PaymentStatus
from app.plans import POCKET_TIERS
from app.services import subscriptions

logger = logging.getLogger(__name__)


async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in get_settings().admin_ids:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception as exc:
            logger.warning("notify admin %s: %s", admin_id, exc)


async def confirm_payment(bot: Bot, session, payment: Payment) -> None:
    """Оплата подтверждена шлюзом: фиксируем покупку и выдаём продукт."""
    if payment.status == PaymentStatus.PAID:
        return
    await repo.set_payment_status(session, payment, PaymentStatus.PAID)
    await repo.add_purchase(
        session,
        user_id=payment.user_id,
        product_type=payment.product_type,
        plan_key=payment.plan_key,
        plan_name=payment.plan_name,
        amount_usd=payment.amount_usd,
        payment_id=payment.id,
    )

    user = await repo.get_user(session, payment.user_id)
    who = user.display_name if user else f"ID:{payment.user_id}"

    if payment.product_type == "vip":
        await subscriptions.grant_vip(bot, session, payment.user_id, payment.plan_key)
        await notify_admins(
            bot,
            f"✅ <b>Оплата подтверждена — VIP выдан автоматически</b>\n\n"
            f"👤 {who}\n🆔 <code>{payment.user_id}</code>\n"
            f"📦 {payment.plan_name} — <b>${payment.amount_usd:.0f}</b>\n"
            f"💳 {payment.gateway} · счёт <code>{payment.external_id}</code>",
        )
    else:
        tier_index = int(payment.plan_key) if payment.plan_key.isdigit() else 0
        tier = POCKET_TIERS[tier_index] if tier_index < len(POCKET_TIERS) else POCKET_TIERS[0]
        await repo.create_pocket_order(
            session,
            user_id=payment.user_id,
            tier_index=tier.index,
            amount_usd=payment.amount_usd,
            balance_usd=tier.balance_usd,
            payment_id=payment.id,
        )
        try:
            await bot.send_message(
                payment.user_id,
                "✅ <b>Ваш платёж подтверждён!</b>\n\n"
                "Аккаунт PocketOption будет выдан в ближайшее время.",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await notify_admins(
            bot,
            f"🏦 <b>Оплачен заказ PocketOption — нужна выдача</b>\n\n"
            f"👤 {who}\n🆔 <code>{payment.user_id}</code>\n"
            f"📦 {payment.plan_name} — <b>${payment.amount_usd:.0f}</b>\n"
            f"➡️ Выдай аккаунт через админку или /admin в боте.",
        )
