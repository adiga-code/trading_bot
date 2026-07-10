"""Тексты бота. Единое место вместо разбросанных строк по хендлерам."""
from __future__ import annotations

from app.plans import POCKET_TIERS, VIP_PLANS

WELCOME = (
    "👋 Добро пожаловать в <b>Forex Trd'K</b>!\n\n"
    "Премиальные крипто-сигналы и готовые аккаунты PocketOption. 📈\n\n"
    "Выберите раздел в меню ниже:"
)

DOCS = "📋 Документы:"


def vip_text() -> str:
    lines = ["💎 <b>VIP Канал — тарифы</b>\n"]
    for p in VIP_PLANS.values():
        period = f"{p.months} мес." if p.months else "Навсегда"
        lines.append(f"• {period} — <b>{p.price_usd:.0f}$</b>  <s>{p.old_price_usd:.0f}$</s>")
    lines.append("\n💳 Оплата: криптовалюта (BTC, ETH, USDT, TON, SOL и др.) или Telegram Stars ⭐️")
    lines.append("Доступ выдаётся после подтверждения оплаты.")
    return "\n".join(lines)


def pocket_text() -> str:
    lines = [
        "🏦 <b>PocketOption — готовые аккаунты</b>\n",
        "Платите меньше — получаете аккаунт с балансом больше:\n",
    ]
    for t in POCKET_TIERS:
        bonus = round((t.balance_usd / t.pay_usd - 1) * 100)
        lines.append(f"• платите <b>{t.pay_usd:.0f}$</b> → баланс <b>{t.balance_usd:.0f}$</b> (+{bonus}%)")
    lines.append("\nАккаунт выдаётся после подтверждения оплаты.")
    return "\n".join(lines)


def payment_method_text(plan_name: str) -> str:
    return (
        "💳 <b>Выберите способ оплаты:</b>\n\n"
        f"📦 {plan_name}\n\n"
        "Оплата: криптовалюта (BTC, ETH, USDT, TON, SOL и др.) "
        "или Telegram Stars ⭐️\n"
        "Доступ выдаётся после подтверждения оплаты."
    )


def fmt_crypto(amount_str: str) -> str:
    """'45.00000000' → '45' — убираем хвостовые нули."""
    try:
        return f"{float(amount_str):.8f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return str(amount_str)


def invoice_text(plan_name: str, payer_amount: str, payer_currency: str, network: str,
                 address: str, expires_at: str) -> str:
    text = (
        "💳 <b>Счёт создан!</b>\n\n"
        f"📦 {plan_name}\n"
        f"💵 Сумма: <b>{fmt_crypto(payer_amount)} {payer_currency}</b> ({network})\n"
    )
    if address:
        text += f"\n🏦 Адрес для оплаты:\n<code>{address}</code>\n"
    if expires_at:
        pretty = expires_at[:16].replace("T", " ")
        text += f"\n⏰ Действует до: {pretty} UTC\n"
    text += "\n🔄 Бот автоматически проверит оплату и уведомит вас."
    return text


STATS_HEADER = "📊 <b>Рынок за 24 часа (Binance)</b>\n\n"
STATS_FOOTER = "\n\n🔄 Данные обновляются в реальном времени"

SUPPORT_TEXT = (
    "🆘 <b>Поддержка</b>\n\n"
    "По всем вопросам пишите напрямую нашему менеджеру:\n"
    "👤 @{support}\n\n"
    "Мы ответим в ближайшее время!"
)
