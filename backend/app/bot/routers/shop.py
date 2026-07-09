"""Выбор тарифа → экран способов оплаты."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.bot import keyboards, texts
from app.plans import POCKET_TIERS, VIP_PLANS

router = Router()


@router.callback_query(F.data == "close")
async def close_message(query: CallbackQuery) -> None:
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass


@router.callback_query(F.data == "show:vip")
async def show_vip(query: CallbackQuery) -> None:
    await query.answer()
    await query.message.edit_text(
        texts.vip_text(), reply_markup=keyboards.vip_plans_kb(with_back=True), parse_mode="HTML"
    )


@router.callback_query(F.data == "show:pocket")
async def show_pocket(query: CallbackQuery) -> None:
    await query.answer()
    await query.message.edit_text(
        texts.pocket_text(), reply_markup=keyboards.pocket_tiers_kb(with_back=True), parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("vip:"))
async def choose_vip_plan(query: CallbackQuery) -> None:
    await query.answer()
    plan_key = query.data.split(":", 1)[1]
    plan = VIP_PLANS.get(plan_key)
    if not plan:
        return
    await query.message.edit_text(
        texts.payment_method_text(plan.name),
        reply_markup=keyboards.payment_methods_kb("vip", plan_key, back_cb="show:vip"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("pocket:"))
async def choose_pocket_tier(query: CallbackQuery) -> None:
    await query.answer()
    key = query.data.split(":", 1)[1]
    try:
        tier = POCKET_TIERS[int(key)]
    except (ValueError, IndexError):
        return
    await query.message.edit_text(
        texts.payment_method_text(tier.name),
        reply_markup=keyboards.payment_methods_kb("pocket", key, back_cb="show:pocket"),
        parse_mode="HTML",
    )
