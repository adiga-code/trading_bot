"""Создание счетов из бота и обработка оплат Telegram Stars."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from app.bot import keyboards, texts
from app.db import repo
from app.db.models import PaymentStatus
from app.payments.base import GatewayError
from app.plans import resolve_plan, resolve_stars
from app.services import payments as payment_service
from app.services.fulfillment import confirm_payment

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("pay:crypto:"))
async def pay_crypto(query: CallbackQuery, session) -> None:
    # pay:crypto:{type}:{plan}:{cur}:{net}
    await query.answer()
    parts = query.data.split(":")
    if len(parts) != 6:
        return
    _, _, product_type, plan_key, currency, network = parts

    await query.message.edit_text("⏳ <b>Создаём счёт на оплату…</b>", parse_mode="HTML")
    try:
        payment, invoice = await payment_service.create_crypto_invoice(
            session,
            user_id=query.from_user.id,
            product_type=product_type,
            plan_key=plan_key,
            currency=currency,
            network=network,
        )
    except GatewayError as exc:
        await query.message.edit_text(
            f"❌ <b>Ошибка создания счёта:</b>\n<code>{exc}</code>\n\nПопробуйте другую криптовалюту.",
            reply_markup=keyboards.back_button(), parse_mode="HTML",
        )
        return

    await query.message.edit_text(
        texts.invoice_text(
            payment.plan_name, invoice.payer_amount, invoice.payer_currency,
            network, invoice.address, invoice.expires_at,
        ),
        reply_markup=keyboards.invoice_kb(invoice.pay_url, invoice.tg_link),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("pay:cryptopay:"))
async def pay_cryptopay(query: CallbackQuery, session) -> None:
    # pay:cryptopay:{type}:{plan}
    await query.answer()
    parts = query.data.split(":")
    if len(parts) != 4:
        return
    _, _, product_type, plan_key = parts

    await query.message.edit_text("⏳ <b>Создаём счёт в Crypto Bot…</b>", parse_mode="HTML")
    try:
        payment, invoice = await payment_service.create_cryptopay_invoice(
            session,
            user_id=query.from_user.id,
            product_type=product_type,
            plan_key=plan_key,
        )
    except GatewayError as exc:
        await query.message.edit_text(
            f"❌ <b>Ошибка Crypto Bot:</b>\n<code>{exc}</code>",
            reply_markup=keyboards.back_button(), parse_mode="HTML",
        )
        return

    await query.message.edit_text(
        texts.cryptopay_invoice_text(payment.plan_name, payment.amount_usd),
        reply_markup=keyboards.invoice_kb(invoice.pay_url),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("pay:stars:"))
async def pay_stars(query: CallbackQuery) -> None:
    # pay:stars:{type}:{plan}
    await query.answer()
    parts = query.data.split(":")
    if len(parts) != 4:
        return
    _, _, product_type, plan_key = parts
    resolved = resolve_stars(product_type, plan_key)
    if not resolved:
        return
    title, stars, payload = resolved

    try:
        await query.bot.send_invoice(
            chat_id=query.message.chat.id,
            title=title,
            description=f"{title} — Forex Trd'K",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=title, amount=stars)],
        )
        await query.message.edit_text(
            f"⭐ <b>{title}</b>\n\nСчёт отправлен — нажмите кнопку оплаты выше.",
            reply_markup=keyboards.back_button(), parse_mode="HTML",
        )
    except Exception as exc:
        logger.error("stars invoice: %s", exc)
        await query.message.edit_text(
            f"❌ Ошибка Stars:\n<code>{exc}</code>",
            reply_markup=keyboards.back_button(), parse_mode="HTML",
        )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def stars_paid(message: Message, session) -> None:
    """Оплата Stars прошла: фиксируем платёж и выдаём продукт автоматически."""
    sp = message.successful_payment
    payload = sp.invoice_payload  # vip_{plan} | pocket_{idx}

    if payload.startswith("pocket_"):
        product_type, plan_key = "pocket", payload.removeprefix("pocket_")
    else:
        product_type, plan_key = "vip", payload.removeprefix("vip_")

    resolved = resolve_plan(product_type, plan_key)
    plan_name, amount_usd = resolved if resolved else (payload, 0.0)

    payment = await repo.create_payment(
        session,
        user_id=message.from_user.id,
        gateway="stars",
        external_id=sp.telegram_payment_charge_id or "",
        product_type=product_type,
        plan_key=plan_key,
        plan_name=f"{plan_name} (⭐ Stars)",
        amount_usd=amount_usd,
        status=PaymentStatus.PENDING,  # confirm_payment переведёт в paid
    )
    await message.answer(
        f"🎉 <b>Оплата прошла!</b>\n\n✅ Получено ⭐ {sp.total_amount}.",
        parse_mode="HTML",
    )
    await confirm_payment(message.bot, session, payment)
