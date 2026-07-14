"""Клиент NicePay (nicepay.io): приём платежей СБП.

СБП принимает только рубли, поэтому сумма из USD переводится по курсу
из настроек (nicepay_usd_rub_rate) — NicePay не отдаёт курс сам.

Важно: верхнеуровневый "status" ответа ("success"/"error" — успех ли сам
запрос к API) и числовой "status" платежа внутри "data" (см.
PAID_STATUSES/FINAL_STATUSES) — это два разных поля с одинаковым именем,
их нельзя путать.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone

import aiohttp

from app.config import get_settings
from app.payments.base import GatewayError, Invoice

logger = logging.getLogger(__name__)

# Числовые коды статуса платежа (см. "Статусы платежей" в документации NicePay)
PAID_STATUSES = {5}
FINAL_STATUSES = {5, 82, 92, 95, 96}


class NicePay:
    def __init__(self, session: aiohttp.ClientSession):
        self._http = session
        s = get_settings()
        self._merchant_id = s.nicepay_merchant_id
        self._secret = s.nicepay_secret_key
        self._base_url = s.nicepay_base_url
        self._rub_rate = s.nicepay_usd_rub_rate

    async def _post(self, method: str, body: dict) -> dict:
        payload = {"merchant_id": self._merchant_id, "secret": self._secret, **body}
        async with self._http.post(
            f"{self._base_url}/{method}",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            return await resp.json()

    def _usd_to_rub_kopecks(self, amount_usd: float) -> int:
        if not self._rub_rate:
            raise GatewayError("Курс USD→RUB не настроен")
        return round(amount_usd * self._rub_rate * 100)

    async def create_invoice(
        self, *, amount_usd: float, order_id: str, description: str, customer: str,
    ) -> Invoice:
        amount_kopecks = self._usd_to_rub_kopecks(amount_usd)
        body = {
            "order_id": order_id[:50],
            "customer": customer[:50],
            "amount": amount_kopecks,
            "currency": "RUB",
            "method": "sbp_rub",
            "description": description[:150],
        }
        try:
            data = await self._post("payment", body)
        except Exception as exc:
            logger.error("nicepay create_invoice: %s", exc)
            raise GatewayError("Платёжный шлюз недоступен") from exc

        if data.get("status") != "success":
            err = (data.get("data") or {}).get("message") or "Ошибка создания счёта"
            raise GatewayError(str(err))

        res = data.get("data", {})
        payment_id = res.get("payment_id")
        if not payment_id:
            raise GatewayError("Шлюз не вернул ID платежа")

        expires_at = ""
        if res.get("expired"):
            expires_at = datetime.fromtimestamp(int(res["expired"]), tz=timezone.utc).isoformat()

        return Invoice(
            external_id=str(payment_id),
            pay_url=res.get("link", ""),
            payer_amount=f"{amount_kopecks / 100:.2f}",
            payer_currency="RUB",
            expires_at=expires_at,
        )

    async def get_status(self, external_id: str) -> int | None:
        """Числовой статус платежа (см. PAID_STATUSES/FINAL_STATUSES) либо None."""
        try:
            data = await self._post("h2hPaymentInfo", {"payment": external_id})
        except Exception as exc:
            logger.warning("nicepay get_status %s: %s", external_id, exc)
            return None
        if data.get("status") != "success":
            return None
        return (data.get("data") or {}).get("status")

    def verify_webhook(self, params: dict) -> bool:
        """Подпись вебхука: sha256(значения по алфавиту ключей + secret, через "{np}")."""
        received_hash = str(params.get("hash", ""))
        data = {k: v for k, v in params.items() if k != "hash"}
        values = [str(data[k]) for k in sorted(data.keys())] + [self._secret]
        computed = hashlib.sha256("{np}".join(values).encode("utf-8")).hexdigest()
        return hmac.compare_digest(computed, received_hash)
