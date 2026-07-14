"""Фоновая проверка статусов оплат.

Pending-платежи читаются из БД, поэтому проверка переживает рестарт процесса —
в старой версии поллинг жил в памяти и терялся при каждом деплое.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from aiogram import Bot

from app.db import repo
from app.db.models import PaymentStatus, utcnow
from app.db.session import get_sessionmaker
from app.payments import base as base_module
from app.payments import cryptobot as cryptobot_module
from app.payments import nicepay as nicepay_module
from app.payments.base import PENDING_TTL_SECONDS
from app.payments.cryptobot import CryptoBot
from app.payments.gate2328 import Gate2328
from app.payments.nicepay import NicePay
from app.services.fulfillment import confirm_payment
from app.services.http import get_http_session

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30           # сек между проверками
PAYMENT_TTL = timedelta(seconds=PENDING_TTL_SECONDS)  # pending старше — помечаем истёкшим

# gateway -> (PAID_STATUSES, FINAL_STATUSES) — каждый шлюз определяет свой словарь статусов
GATEWAY_STATUSES = {
    "gate2328": (base_module.PAID_STATUSES, base_module.FINAL_STATUSES),
    "cryptobot": (cryptobot_module.PAID_STATUSES, cryptobot_module.FINAL_STATUSES),
    "nicepay": (nicepay_module.PAID_STATUSES, nicepay_module.FINAL_STATUSES),
}


async def _check_once(bot: Bot) -> None:
    http = get_http_session()
    clients = {
        "gate2328": Gate2328(http),
        "cryptobot": CryptoBot(http),
        "nicepay": NicePay(http),
    }

    async with get_sessionmaker()() as session:
        for payment in await repo.pending_payments(session):
            if utcnow() - payment.created_at > PAYMENT_TTL:
                await repo.set_payment_status(session, payment, PaymentStatus.EXPIRED)
                continue

            client = clients.get(payment.gateway)
            statuses = GATEWAY_STATUSES.get(payment.gateway)
            if client is None or statuses is None:
                continue
            paid_statuses, final_statuses = statuses

            status = await client.get_status(payment.external_id)
            if status is None:
                continue
            if status in paid_statuses:
                await confirm_payment(bot, session, payment)
            elif status in final_statuses:
                await repo.set_payment_status(session, payment, PaymentStatus.CANCELLED)


async def watcher_loop(bot: Bot) -> None:
    """Запускается из lifespan приложения."""
    while True:
        try:
            await _check_once(bot)
        except Exception as exc:
            logger.exception("payment watcher: %s", exc)
        await asyncio.sleep(CHECK_INTERVAL)
