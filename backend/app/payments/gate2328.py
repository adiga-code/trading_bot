"""Клиент 2328.io: приём крипто-платежей.

Подпись: HMAC-SHA256(api_key, base64(compact_json_body)) — подписываются
ровно те байты, которые уходят в запрос, поэтому тело сериализуется один раз.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging

import aiohttp

from app.config import get_settings
from app.payments.base import GatewayError, Invoice

logger = logging.getLogger(__name__)


def sign_body(api_key: str, body_json: str) -> str:
    body_b64 = base64.b64encode(body_json.encode("utf-8")).decode("utf-8")
    return hmac.new(api_key.encode("utf-8"), body_b64.encode("utf-8"), hashlib.sha256).hexdigest()


class Gate2328:
    def __init__(self, session: aiohttp.ClientSession):
        self._http = session
        s = get_settings()
        self._api_key = s.gate2328_api_key
        self._project_id = s.gate2328_project_id
        self._base_url = s.gate2328_base_url
        self._callback_url = s.payment_callback_url

    async def _post(self, path: str, body: dict) -> dict:
        body_json = json.dumps(body, separators=(",", ":"), ensure_ascii=True)
        headers = {
            "Content-Type": "application/json",
            "project": self._project_id,
            "sign": sign_body(self._api_key, body_json),
            "User-Agent": "ForexTrdK/2.0",
        }
        async with self._http.post(
            f"{self._base_url}{path}",
            data=body_json.encode("utf-8"),  # именно подписанные байты, не json=
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            return await resp.json()

    async def create_invoice(
        self,
        *,
        amount_usd: float,
        order_id: str,
        description: str,
        to_currency: str,
        network: str,
    ) -> Invoice:
        body: dict = {
            "amount": f"{amount_usd:.2f}",
            "currency": "USD",
            "order_id": order_id,
            "description": description[:200],
            "to_currency": to_currency,
            "network": network,
        }
        if self._callback_url:
            body["url_callback"] = self._callback_url

        try:
            data = await self._post("/payment", body)
        except Exception as exc:
            logger.error("2328 create_invoice: %s", exc)
            raise GatewayError("Платёжный шлюз недоступен") from exc

        if data.get("state") != 0:
            err = data.get("message") or data.get("error") or "Ошибка создания счёта"
            raise GatewayError(str(err))

        res = data.get("result", {})
        return Invoice(
            external_id=res.get("uuid") or order_id,
            pay_url=res.get("url", ""),
            tg_link=res.get("tg_deeplink", ""),
            address=res.get("address", ""),
            payer_amount=str(res.get("payer_amount", "")),
            payer_currency=res.get("payer_currency", to_currency),
            expires_at=res.get("expires_at", ""),
        )

    async def get_status(self, external_id: str) -> str | None:
        """payment_status счёта либо None, если шлюз не ответил."""
        try:
            data = await self._post("/payment/info", {"uuid": external_id})
        except Exception as exc:
            logger.warning("2328 get_status %s: %s", external_id, exc)
            return None
        if data.get("state") != 0:
            return None
        return (data.get("result") or {}).get("payment_status", "")
