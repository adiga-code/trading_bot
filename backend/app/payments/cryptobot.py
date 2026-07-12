"""Клиент @CryptoBot (Crypto Pay API): https://help.crypt.bot/crypto-pay-api

Инвойс выставляется в фиате (USD) — конкретную монету для оплаты покупатель
выбирает уже на странице CryptoBot, поэтому здесь не нужен выбор сети/валюты.
"""
from __future__ import annotations

import logging

import aiohttp

from app.config import get_settings
from app.payments.base import GatewayError, Invoice, PENDING_TTL_SECONDS

logger = logging.getLogger(__name__)

PAID_STATUSES = {"paid"}
FINAL_STATUSES = {"paid", "expired"}


class CryptoBot:
    def __init__(self, session: aiohttp.ClientSession):
        self._http = session
        s = get_settings()
        self._token = s.cryptobot_api_token
        self._base_url = s.cryptobot_base_url

    async def _post(self, method: str, body: dict) -> dict:
        headers = {"Crypto-Pay-API-Token": self._token}
        async with self._http.post(
            f"{self._base_url}/{method}",
            json=body,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            return await resp.json()

    async def create_invoice(self, *, amount_usd: float, order_id: str, description: str) -> Invoice:
        body = {
            "currency_type": "fiat",
            "fiat": "USD",
            "amount": f"{amount_usd:.2f}",
            "description": description[:1024],
            "payload": order_id,
            "allow_comments": False,
            "allow_anonymous": False,
            # Инвойс должен истечь не позже, чем watcher перестанет опрашивать
            # его локальный статус (см. PENDING_TTL_SECONDS) — иначе покупатель
            # может оплатить уже после того, как платёж помечен истёкшим у нас.
            "expires_in": PENDING_TTL_SECONDS,
        }
        try:
            data = await self._post("createInvoice", body)
        except Exception as exc:
            logger.error("cryptobot create_invoice: %s", exc)
            raise GatewayError("Платёжный шлюз недоступен") from exc

        if not data.get("ok"):
            err = (data.get("error") or {}).get("name") or "Ошибка создания счёта"
            raise GatewayError(str(err))

        res = data.get("result", {})
        invoice_id = res.get("invoice_id")
        if invoice_id is None:
            raise GatewayError("Шлюз не вернул ID счёта")

        pay_url = res.get("mini_app_invoice_url") or res.get("bot_invoice_url") or res.get("pay_url", "")
        return Invoice(
            external_id=str(invoice_id),
            pay_url=pay_url,
            tg_link=res.get("bot_invoice_url", ""),
            payer_amount=str(res.get("amount", f"{amount_usd:.2f}")),
            payer_currency="USD",
            expires_at=res.get("expiration_date", ""),
        )

    async def get_status(self, external_id: str) -> str | None:
        """status инвойса либо None, если шлюз не ответил."""
        try:
            data = await self._post("getInvoices", {"invoice_ids": external_id})
        except Exception as exc:
            logger.warning("cryptobot get_status %s: %s", external_id, exc)
            return None
        if not data.get("ok"):
            return None
        items = (data.get("result") or {}).get("items") or []
        return items[0].get("status") if items else None
