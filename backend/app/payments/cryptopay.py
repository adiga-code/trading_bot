"""Клиент Crypto Bot (CryptoPay) — счета в @CryptoBot."""
from __future__ import annotations

import logging

import aiohttp

from app.config import get_settings
from app.payments.base import GatewayError, Invoice

logger = logging.getLogger(__name__)


class CryptoPay:
    def __init__(self, session: aiohttp.ClientSession):
        self._http = session
        s = get_settings()
        self._token = s.cryptopay_token
        self._base_url = s.cryptopay_base_url

    @property
    def _headers(self) -> dict:
        return {"Crypto-Pay-API-Token": self._token}

    async def create_invoice(self, *, amount_usd: float, description: str, payload: str) -> Invoice:
        body = {
            "currency_type": "fiat",
            "fiat": "USD",
            "amount": f"{amount_usd:.2f}",
            "description": description[:1024],
            "payload": payload[:4000],
            "expires_in": 3600,
        }
        try:
            async with self._http.post(
                f"{self._base_url}/createInvoice",
                json=body,
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()
        except Exception as exc:
            logger.error("cryptopay create_invoice: %s", exc)
            raise GatewayError("Crypto Bot недоступен") from exc

        if not data.get("ok"):
            err = (data.get("error") or {}).get("name") or "Ошибка Crypto Bot"
            raise GatewayError(str(err))

        inv = data.get("result", {})
        return Invoice(
            external_id=str(inv.get("invoice_id", "")),
            pay_url=inv.get("bot_invoice_url", ""),
            tg_link=inv.get("bot_invoice_url", ""),
        )

    async def get_status(self, invoice_id: str) -> str | None:
        """active | paid | expired либо None, если API не ответил."""
        try:
            async with self._http.get(
                f"{self._base_url}/getInvoices",
                params={"invoice_ids": invoice_id},
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()
        except Exception as exc:
            logger.warning("cryptopay get_status %s: %s", invoice_id, exc)
            return None
        if not data.get("ok"):
            return None
        items = (data.get("result") or {}).get("items", [])
        return items[0].get("status", "") if items else None
