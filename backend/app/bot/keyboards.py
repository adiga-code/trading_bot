from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.config import get_settings
from app.plans import CRYPTO_OPTIONS, POCKET_TIERS, VIP_PLANS

BTN_VIP = "💎 VIP - канал"
BTN_POCKET = "🏦 PocketOption"
BTN_STATS = "📊 Статистика"
BTN_SUPPORT = "🆘 Поддержка"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_VIP), KeyboardButton(text=BTN_POCKET)],
            [KeyboardButton(text=BTN_STATS), KeyboardButton(text=BTN_SUPPORT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def policy_links() -> InlineKeyboardMarkup:
    s = get_settings()
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔒 Политика конфиденциальности", url=s.privacy_url),
        InlineKeyboardButton(text="📜 Пользовательское соглашение", url=s.terms_url),
    ]])


def back_button(cb: str = "close") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="◀️ Назад", callback_data=cb)
    ]])


def vip_plans_kb(with_back: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{p.name} — {p.price_usd:.0f}$",
            callback_data=f"vip:{p.key}",
        )]
        for p in VIP_PLANS.values()
    ]
    if with_back:
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pocket_tiers_kb(with_back: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{t.pay_usd:.0f}$ → {t.balance_usd:.0f}$",
            callback_data=f"pocket:{t.index}",
        )]
        for t in POCKET_TIERS
    ]
    if with_back:
        rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data="close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def payment_methods_kb(product_type: str, plan_key: str, back_cb: str) -> InlineKeyboardMarkup:
    """Сетка криптовалют + Stars. Формат cb: pay:crypto:{type}:{plan}:{cur}:{net}"""
    rows: list[list[InlineKeyboardButton]] = []
    for i in range(0, len(CRYPTO_OPTIONS), 2):
        row = [
            InlineKeyboardButton(
                text=label,
                callback_data=f"pay:crypto:{product_type}:{plan_key}:{cur}:{net}",
            )
            for label, cur, net in CRYPTO_OPTIONS[i:i + 2]
        ]
        rows.append(row)
    rows.append([InlineKeyboardButton(
        text="💎 CryptoBot",
        callback_data=f"pay:cryptobot:{product_type}:{plan_key}",
    )])
    rows.append([InlineKeyboardButton(
        text="🏦 СБП",
        callback_data=f"pay:nicepay:{product_type}:{plan_key}",
    )])
    rows.append([InlineKeyboardButton(
        text="Telegram Stars ⭐️",
        callback_data=f"pay:stars:{product_type}:{plan_key}",
    )])
    rows.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def invoice_kb(pay_url: str, tg_link: str = "") -> InlineKeyboardMarkup:
    btns = []
    if pay_url:
        btns.append(InlineKeyboardButton(text="💳 Оплатить онлайн", url=pay_url))
    if tg_link and tg_link != pay_url:
        btns.append(InlineKeyboardButton(text="⚡ Оплата в Telegram", url=tg_link))
    rows = ([btns] if btns else []) + [[InlineKeyboardButton(text="◀️ Назад", callback_data="close")]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Админ-клавиатуры ─────────────────────────────────────────────────────────

def admin_user_actions(uid: int, is_vip: bool) -> InlineKeyboardMarkup:
    toggle = (
        InlineKeyboardButton(text="🚫 Убрать VIP", callback_data=f"adm:unvip:{uid}")
        if is_vip
        else InlineKeyboardButton(text="💎 Выдать VIP", callback_data=f"adm:vip:{uid}")
    )
    return InlineKeyboardMarkup(inline_keyboard=[
        [toggle, InlineKeyboardButton(text="✉️ Написать", callback_data=f"adm:reply:{uid}")],
        [InlineKeyboardButton(text="📦 Выдать PocketOption", callback_data=f"adm:pocket:{uid}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="adm:panel")],
    ])


def admin_vip_plans(uid: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=p.name, callback_data=f"adm:vipgrant:{uid}:{p.key}")]
        for p in VIP_PLANS.values()
    ]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="adm:panel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_notify_actions(uid: int) -> InlineKeyboardMarkup:
    """Кнопки под уведомлением об оплате/сообщении."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="👤 Пользователь", callback_data=f"adm:info:{uid}"),
        InlineKeyboardButton(text="✉️ Написать", callback_data=f"adm:reply:{uid}"),
    ]])


def admin_pocket_notify_actions(uid: int) -> InlineKeyboardMarkup:
    """Кнопки под уведомлением о купленном PocketOption: выдача в один тап."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Выдать аккаунт", callback_data=f"adm:pocket:{uid}")],
        [
            InlineKeyboardButton(text="👤 Пользователь", callback_data=f"adm:info:{uid}"),
            InlineKeyboardButton(text="✉️ Написать", callback_data=f"adm:reply:{uid}"),
        ],
    ])
