from __future__ import annotations

from dataclasses import dataclass


class GatewayError(Exception):
    """Шлюз ответил ошибкой или недоступен. message показывается пользователю."""


@dataclass
class Invoice:
    """Созданный счёт — единый формат для всех шлюзов."""

    external_id: str
    pay_url: str = ""
    tg_link: str = ""            # deeplink для оплаты внутри Telegram
    address: str = ""            # крипто-адрес для прямого перевода
    payer_amount: str = ""       # сумма в криптовалюте
    payer_currency: str = ""
    expires_at: str = ""         # ISO-строка от шлюза


# Статусы 2328.io, означающие успешную оплату / финальное состояние
PAID_STATUSES = {"paid", "overpaid"}
FINAL_STATUSES = {"paid", "overpaid", "cancel", "aml_lock", "underpaid", "expired"}

# Через сколько секунд watcher помечает pending-платёж истёкшим (см. watcher.PAYMENT_TTL).
# Шлюзы, у которых можно задать TTL самого счёта (CryptoBot), обязаны выставлять его
# не длиннее этого значения — иначе счёт останется оплачиваемым уже после того, как
# локальная запись в БД истечёт и перестанет опрашиваться.
PENDING_TTL_SECONDS = 7200
