"""Вебхуки внешних платёжных шлюзов. Авторизация — подпись запроса, не initData."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app import runtime
from app.api.deps import db_session
from app.db import repo
from app.db.models import PaymentStatus
from app.payments.nicepay import NicePay
from app.services.fulfillment import confirm_payment
from app.services.http import get_http_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("/nicepay")
async def nicepay_webhook(request: Request, session: AsyncSession = Depends(db_session)):
    params = dict(request.query_params)
    gateway = NicePay(get_http_session())

    if not gateway.verify_webhook(params):
        logger.warning("nicepay webhook: invalid hash, payment_id=%s", params.get("payment_id"))
        return {"error": {"message": "Invalid hash"}}

    payment = await repo.get_pending_payment_by_external_id(
        session, "nicepay", params.get("payment_id", ""),
    )
    if not payment:
        return {"result": {"message": "Unknown payment"}}

    if params.get("result") == "success":
        try:
            bot = runtime.get_bot()
        except RuntimeError:
            return {"error": {"message": "Bot is not configured"}}
        await confirm_payment(bot, session, payment)
    else:
        await repo.set_payment_status(session, payment, PaymentStatus.CANCELLED)

    return {"result": {"message": "Success"}}
