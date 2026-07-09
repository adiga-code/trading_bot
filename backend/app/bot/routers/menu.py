"""Экраны из нижнего reply-меню."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import keyboards, texts
from app.config import get_settings
from app.plans import TRADING_PAIRS
from app.services.market import binance_24h_changes

router = Router()


def _stats_text(prices: dict[str, float]) -> str:
    rows = []
    for pair in TRADING_PAIRS:
        if pair in prices:
            change = prices[pair]
            emoji = "🟢" if change >= 0 else "🔻"
            sign = "+" if change >= 0 else ""
            rows.append(f"<code>{pair:<12}</code>: {sign}{change:.2f}% {emoji}")
        else:
            rows.append(f"<code>{pair:<12}</code>: N/A ❓")
    return texts.STATS_HEADER + "\n".join(rows) + texts.STATS_FOOTER


def _refresh_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔄 Обновить", callback_data="stats:refresh")
    ]])


@router.message(F.text == keyboards.BTN_VIP)
async def screen_vip(message: Message) -> None:
    await message.answer(texts.vip_text(), reply_markup=keyboards.vip_plans_kb(), parse_mode="HTML")


@router.message(F.text == keyboards.BTN_POCKET)
async def screen_pocket(message: Message) -> None:
    await message.answer(texts.pocket_text(), reply_markup=keyboards.pocket_tiers_kb(), parse_mode="HTML")


@router.message(F.text == keyboards.BTN_STATS)
async def screen_stats(message: Message) -> None:
    wait = await message.answer("⏳ Загрузка актуальных цен с Binance...")
    prices = await binance_24h_changes(TRADING_PAIRS)
    await wait.edit_text(_stats_text(prices), reply_markup=_refresh_kb(), parse_mode="HTML")


@router.callback_query(F.data == "stats:refresh")
async def stats_refresh(query: CallbackQuery) -> None:
    await query.answer("Обновляю…")
    prices = await binance_24h_changes(TRADING_PAIRS)
    try:
        await query.message.edit_text(_stats_text(prices), reply_markup=_refresh_kb(), parse_mode="HTML")
    except Exception:
        pass  # текст не изменился — Telegram не даёт редактировать без изменений


@router.message(F.text == keyboards.BTN_SUPPORT)
async def screen_support(message: Message) -> None:
    s = get_settings()
    await message.answer(
        texts.SUPPORT_TEXT.format(support=s.support_username),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✉️ Написать в поддержку", url=f"https://t.me/{s.support_username}")
        ]]),
        parse_mode="HTML",
    )
