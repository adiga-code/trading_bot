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
from app.payments.base import FINAL_STATUSES, PAID_STATUSES
from app.payments.gate2328 import Gate2328
from app.services.fulfillment import confirm_payment
from app.services.http import get_http_session

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 30           # сек между проверками
PAYMENT_TTL = timedelta(hours=2)  # pending старше — помечаем истёкшим


async def _check_once(bot: Bot) -> None:
    http = get_http_session()
    gate2328 = Gate2328(http)

    async with get_sessionmaker()() as session:
        for payment in await repo.pending_payments(session):
            if utcnow() - payment.created_at > PAYMENT_TTL:
                await repo.set_payment_status(session, payment, PaymentStatus.EXPIRED)
                continue

            if payment.gateway == "gate2328":
                status = await gate2328.get_status(payment.external_id)
                if status is None:
                    continue
                if status in PAID_STATUSES:
                    await confirm_payment(bot, session, payment)
                elif status in FINAL_STATUSES:
                    await repo.set_payment_status(session, payment, PaymentStatus.CANCELLED)


async def watcher_loop(bot: Bot) -> None:
    """Запускается из lifespan приложения."""
    while True:
        try:
            await _check_once(bot)
        except Exception as exc:
            logger.exception("payment watcher: %s", exc)
        await asyncio.sleep(CHECK_INTERVAL)
