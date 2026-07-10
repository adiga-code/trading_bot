"""Что происходит после подтверждения оплаты: покупка, выдача, уведомления."""
from __future__ import annotations

import logging

from aiogram import Bot

from app.bot import keyboards
from app.db import repo
from app.db.models import Payment, PaymentStatus, utcnow
from app.plans import POCKET_TIERS
from app.services import subscriptions
from app.services.subscriptions import notify_admins

logger = logging.getLogger(__name__)

GATEWAY_LABELS = {"gate2328": "криптовалюта (2328.io)", "stars": "Telegram Stars ⭐️"}


def _buyer_card(payment: Payment, user) -> str:
    """Полная карточка покупателя для уведомления админу."""
    lines = []
    if user:
        lines.append(f"👤 Имя: {user.display_name}")
        if user.username:
            lines.append(f"🔗 Юзернейм: @{user.username}")
    else:
        lines.append("👤 Имя: неизвестно")
    lines.append(f"🆔 Telegram ID: <code>{payment.user_id}</code>")
    lines.append(f"📦 Товар: {payment.plan_name}")
    lines.append(f"💵 Цена: <b>{payment.amount_usd:.0f}$</b>")
    lines.append(f"💳 Оплата: {GATEWAY_LABELS.get(payment.gateway, payment.gateway)}")
    if payment.external_id:
        lines.append(f"🧾 Счёт: <code>{payment.external_id}</code>")
    lines.append(f"📅 Дата: {utcnow():%d.%m.%Y %H:%M} UTC")
    return "\n".join(lines)


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

    if payment.product_type == "vip":
        await subscriptions.grant_vip(bot, session, payment.user_id, payment.plan_key)
        await notify_admins(
            bot,
            "✅ <b>Куплена VIP-подписка — доступ выдан автоматически</b>\n\n"
            + _buyer_card(payment, user),
            reply_markup=keyboards.admin_notify_actions(payment.user_id),
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
            "🏦 <b>Куплен аккаунт PocketOption — нужна выдача</b>\n\n"
            + _buyer_card(payment, user)
            + "\n\n➡️ Нажми «Выдать аккаунт» и впиши данные для входа — бот отправит их покупателю.",
            reply_markup=keyboards.admin_pocket_notify_actions(payment.user_id),
        )
