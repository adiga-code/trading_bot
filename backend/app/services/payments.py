"""Создание счетов: единая точка для бота и Mini App API."""
from __future__ import annotations

import time

from app.config import get_settings
from app.db import repo
from app.db.models import Payment
from app.payments.base import GatewayError, Invoice
from app.payments.cryptopay import CryptoPay
from app.payments.gate2328 import Gate2328
from app.plans import resolve_plan
from app.services.http import get_http_session


def _description(plan_name: str) -> str:
    return f"{plan_name} — {get_settings().brand_name}"


async def create_crypto_invoice(
    session,
    *,
    user_id: int,
    product_type: str,
    plan_key: str,
    currency: str,
    network: str,
) -> tuple[Payment, Invoice]:
    resolved = resolve_plan(product_type, plan_key)
    if not resolved:
        raise GatewayError("Неизвестный тариф")
    plan_name, amount = resolved

    gateway = Gate2328(get_http_session())
    invoice = await gateway.create_invoice(
        amount_usd=amount,
        order_id=f"{user_id}_{int(time.time())}",
        description=_description(plan_name),
        to_currency=currency,
        network=network,
    )
    payment = await repo.create_payment(
        session,
        user_id=user_id,
        gateway="gate2328",
        external_id=invoice.external_id,
        product_type=product_type,
        plan_key=plan_key,
        plan_name=plan_name,
        amount_usd=amount,
        pay_url=invoice.pay_url,
    )
    return payment, invoice


async def create_cryptopay_invoice(
    session,
    *,
    user_id: int,
    product_type: str,
    plan_key: str,
) -> tuple[Payment, Invoice]:
    resolved = resolve_plan(product_type, plan_key)
    if not resolved:
        raise GatewayError("Неизвестный тариф")
    plan_name, amount = resolved

    gateway = CryptoPay(get_http_session())
    invoice = await gateway.create_invoice(
        amount_usd=amount,
        description=_description(plan_name),
        payload=f"{user_id}_{product_type}_{plan_key}",
    )
    payment = await repo.create_payment(
        session,
        user_id=user_id,
        gateway="cryptopay",
        external_id=invoice.external_id,
        product_type=product_type,
        plan_key=plan_key,
        plan_name=plan_name,
        amount_usd=amount,
        pay_url=invoice.pay_url,
    )
    return payment, invoice
