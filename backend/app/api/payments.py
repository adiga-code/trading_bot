"""Платёжные эндпоинты Mini App. Все требуют валидный Telegram initData."""
from __future__ import annotations

from aiogram.types import LabeledPrice
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import runtime
from app.api.auth import WebAppUser, current_user
from app.api.deps import db_session
from app.db import repo
from app.payments.base import GatewayError
from app.plans import resolve_stars
from app.services import payments as payment_service

router = APIRouter(prefix="/api", tags=["payments"])


class PayRequest(BaseModel):
    type: str            # vip | pocket
    plan: str
    cur: str = "USDT"
    net: str = "TRX-TRC20"


class CryptoPayRequest(BaseModel):
    type: str
    plan: str


class StarsRequest(BaseModel):
    type: str
    plan: str


@router.post("/pay")
async def create_pay(
    body: PayRequest,
    user: WebAppUser = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    await repo.upsert_user(session, user.id, user.username, user.first_name, user.last_name)
    try:
        payment, invoice = await payment_service.create_crypto_invoice(
            session,
            user_id=user.id,
            product_type=body.type,
            plan_key=body.plan,
            currency=body.cur,
            network=body.net,
        )
    except GatewayError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "url": invoice.pay_url,
        "tg_link": invoice.tg_link,
        "address": invoice.address,
        "payer_amount": invoice.payer_amount or "?",
        "payer_currency": invoice.payer_currency,
        "uuid": invoice.external_id,
        "expires_at": invoice.expires_at,
    }


@router.post("/cryptopay")
async def create_cryptopay(
    body: CryptoPayRequest,
    user: WebAppUser = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    await repo.upsert_user(session, user.id, user.username, user.first_name, user.last_name)
    try:
        payment, invoice = await payment_service.create_cryptopay_invoice(
            session,
            user_id=user.id,
            product_type=body.type,
            plan_key=body.plan,
        )
    except GatewayError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "invoice_id": invoice.external_id,
        "bot_invoice_url": invoice.pay_url,
    }


@router.post("/stars")
async def create_stars_invoice(
    body: StarsRequest,
    user: WebAppUser = Depends(current_user),
):
    """Ссылка-инвойс Telegram Stars — фронт открывает её через tg.openInvoice()."""
    resolved = resolve_stars(body.type, body.plan)
    if not resolved:
        raise HTTPException(status_code=400, detail="Unknown plan")
    title, stars, payload = resolved
    try:
        bot = runtime.get_bot()
        link = await bot.create_invoice_link(
            title=title,
            description=f"{title} — Forex Trd'K",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(label=title, amount=stars)],
        )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Bot is not configured")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Stars error: {exc}")
    return {"link": link}
