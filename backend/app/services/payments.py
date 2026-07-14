"""Создание счетов: единая точка для бота и Mini App API."""
from __future__ import annotations

import time

from app.config import get_settings
from app.db import repo
from app.db.models import Payment
from app.payments.base import GatewayError, Invoice
from app.payments.cryptobot import CryptoBot
from app.payments.gate2328 import Gate2328
from app.payments.nicepay import NicePay
from app.plans import resolve_plan
from app.services.http import get_http_session


def _description(plan_name: str) -> str:
    return f"{plan_name} — {get_settings().brand_name}"


def _resolve_plan_or_raise(product_type: str, plan_key: str) -> tuple[str, float]:
    resolved = resolve_plan(product_type, plan_key)
    if not resolved:
        raise GatewayError("Неизвестный тариф")
    return resolved


async def _record_payment(
    session,
    *,
    gateway: str,
    invoice: Invoice,
    user_id: int,
    product_type: str,
    plan_key: str,
    plan_name: str,
    amount: float,
) -> Payment:
    return await repo.create_payment(
        session,
        user_id=user_id,
        gateway=gateway,
        external_id=invoice.external_id,
        product_type=product_type,
        plan_key=plan_key,
        plan_name=plan_name,
        amount_usd=amount,
        pay_url=invoice.pay_url,
    )


async def create_crypto_invoice(
    session,
    *,
    user_id: int,
    product_type: str,
    plan_key: str,
    currency: str,
    network: str,
) -> tuple[Payment, Invoice]:
    plan_name, amount = _resolve_plan_or_raise(product_type, plan_key)

    gateway = Gate2328(get_http_session())
    invoice = await gateway.create_invoice(
        amount_usd=amount,
        order_id=f"{user_id}_{int(time.time())}",
        description=_description(plan_name),
        to_currency=currency,
        network=network,
    )
    payment = await _record_payment(
        session, gateway="gate2328", invoice=invoice, user_id=user_id,
        product_type=product_type, plan_key=plan_key, plan_name=plan_name, amount=amount,
    )
    return payment, invoice


async def create_cryptobot_invoice(
    session,
    *,
    user_id: int,
    product_type: str,
    plan_key: str,
) -> tuple[Payment, Invoice]:
    plan_name, amount = _resolve_plan_or_raise(product_type, plan_key)

    gateway = CryptoBot(get_http_session())
    invoice = await gateway.create_invoice(
        amount_usd=amount,
        order_id=f"{user_id}_{int(time.time())}",
        description=_description(plan_name),
    )
    payment = await _record_payment(
        session, gateway="cryptobot", invoice=invoice, user_id=user_id,
        product_type=product_type, plan_key=plan_key, plan_name=plan_name, amount=amount,
    )
    return payment, invoice


async def create_nicepay_invoice(
    session,
    *,
    user_id: int,
    product_type: str,
    plan_key: str,
    customer: str,
) -> tuple[Payment, Invoice]:
    plan_name, amount = _resolve_plan_or_raise(product_type, plan_key)

    gateway = NicePay(get_http_session())
    invoice = await gateway.create_invoice(
        amount_usd=amount,
        order_id=f"{user_id}_{int(time.time())}",
        description=_description(plan_name),
        customer=customer,
    )
    payment = await _record_payment(
        session, gateway="nicepay", invoice=invoice, user_id=user_id,
        product_type=product_type, plan_key=plan_key, plan_name=plan_name, amount=amount,
    )
    return payment, invoice
