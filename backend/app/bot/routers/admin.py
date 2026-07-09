"""Админ-панель в боте: статистика, пользователи, выдача VIP/Pocket, ответы."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot import keyboards
from app.config import get_settings
from app.db import repo
from app.services import subscriptions

logger = logging.getLogger(__name__)

router = Router()


def _is_admin(user_id: int) -> bool:
    return get_settings().is_admin(user_id)


# фильтруем весь роутер: сюда попадают только админы
router.message.filter(lambda m: bool(m.from_user and _is_admin(m.from_user.id)))
router.callback_query.filter(lambda q: bool(q.from_user and _is_admin(q.from_user.id)))


class AdminStates(StatesGroup):
    reply_to_user = State()    # ждём текст ответа пользователю
    pocket_for_user = State()  # ждём данные аккаунта PocketOption


async def _panel_content(session) -> tuple[str, InlineKeyboardMarkup]:
    total_users = await repo.count_users(session)
    vip_count = await repo.count_vip_users(session)
    purchases_count, revenue = await repo.purchases_stats(session)

    text = (
        "👑 <b>Админ Панель — Forex Trd'K</b>\n\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"💎 VIP активных: <b>{vip_count}</b>\n"
        f"💰 Покупок: <b>{purchases_count}</b> на <b>${revenue:.0f}</b>\n\n"
        "Полная админка — в Mini App (вкладка «Админ»)."
    )

    recent = await repo.list_users(session, limit=5)
    user_rows = [
        [InlineKeyboardButton(
            text=f"{'✅' if u.is_vip else '➕'} {u.display_name[:20]}",
            callback_data=f"adm:info:{u.id}",
        )]
        for u in recent
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Все пользователи", callback_data="adm:users"),
            InlineKeyboardButton(text="💰 Покупки", callback_data="adm:purchases"),
        ],
        *user_rows,
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="adm:panel")],
    ])
    return text, kb


@router.message(Command("admin"))
async def cmd_admin(message: Message, session) -> None:
    text, kb = await _panel_content(session)
    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "adm:panel")
async def panel_refresh(query: CallbackQuery, session, state: FSMContext) -> None:
    await query.answer()
    await state.clear()
    text, kb = await _panel_content(session)
    try:
        await query.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    except Exception:
        pass


@router.callback_query(F.data == "adm:users")
async def panel_users(query: CallbackQuery, session) -> None:
    await query.answer()
    users = await repo.list_users(session, limit=30)
    total = await repo.count_users(session)
    lines = ["👥 <b>Все пользователи:</b>\n"]
    for u in users:
        badge = " 💎" if u.is_vip else ""
        lines.append(f"• {u.display_name}{badge} — <code>{u.id}</code> — {u.created_at:%d.%m.%Y}")
    if total > 30:
        lines.append(f"\n… и ещё {total - 30}")
    await query.message.edit_text(
        "\n".join(lines),
        reply_markup=keyboards.back_button("adm:panel"),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "adm:purchases")
async def panel_purchases(query: CallbackQuery, session) -> None:
    await query.answer()
    purchases = await repo.list_purchases(session, limit=20)
    lines = ["💰 <b>Последние покупки:</b>\n"]
    for purchase, user in purchases:
        who = user.display_name if user else f"ID:{purchase.user_id}"
        lines.append(f"• {who} — {purchase.plan_name} (${purchase.amount_usd:.0f}) — {purchase.created_at:%d.%m.%Y}")
    if not purchases:
        lines.append("Покупок пока нет.")
    await query.message.edit_text(
        "\n".join(lines),
        reply_markup=keyboards.back_button("adm:panel"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("adm:info:"))
async def user_info(query: CallbackQuery, session) -> None:
    await query.answer()
    uid = int(query.data.rsplit(":", 1)[1])
    user = await repo.get_user(session, uid)
    if not user:
        await query.answer("Пользователь не найден", show_alert=True)
        return
    sub = await repo.active_subscription(session, uid)
    if user.is_vip and sub:
        vip_label = "✅ VIP до " + (f"{sub.expires_at:%d.%m.%Y}" if sub.expires_at else "∞ (навсегда)")
    else:
        vip_label = "✅ VIP активен" if user.is_vip else "❌ VIP не активен"
    await query.message.edit_text(
        f"👤 <b>Пользователь</b>\n\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"👤 Имя: {user.display_name}\n"
        f"📅 Дата: {user.created_at:%d.%m.%Y}\n"
        f"💎 Статус: {vip_label}",
        reply_markup=keyboards.admin_user_actions(uid, user.is_vip),
        parse_mode="HTML",
    )


# ── Выдача VIP: выбор тарифа → автовыдача через сервис подписок ──────────────

@router.callback_query(F.data.startswith("adm:vip:"))
async def vip_choose_plan(query: CallbackQuery) -> None:
    await query.answer()
    uid = int(query.data.rsplit(":", 1)[1])
    await query.message.edit_text(
        f"💎 <b>Выдача VIP</b> пользователю <code>{uid}</code>\n\nВыберите тариф:",
        reply_markup=keyboards.admin_vip_plans(uid),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("adm:vipgrant:"))
async def vip_grant(query: CallbackQuery, session) -> None:
    # adm:vipgrant:{uid}:{plan_key}
    parts = query.data.split(":")
    uid, plan_key = int(parts[2]), parts[3]
    await query.answer("Выдаю…")
    sub = await subscriptions.grant_vip(query.bot, session, uid, plan_key)
    until = f"до {sub.expires_at:%d.%m.%Y}" if sub.expires_at else "навсегда"
    await query.message.edit_text(
        f"✅ VIP выдан пользователю <code>{uid}</code> ({until}).\n"
        f"Инвайт в канал отправлен автоматически.",
        reply_markup=keyboards.back_button("adm:panel"),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("adm:unvip:"))
async def vip_revoke(query: CallbackQuery, session) -> None:
    uid = int(query.data.rsplit(":", 1)[1])
    sub = await repo.active_subscription(session, uid)
    if sub:
        await subscriptions.revoke_vip(query.bot, session, sub, notify=False)
    else:
        await repo.set_vip(session, uid, False)
    await query.answer("VIP снят", show_alert=True)
    await query.message.edit_text(
        f"🚫 VIP снят у пользователя <code>{uid}</code>.",
        reply_markup=keyboards.back_button("adm:panel"),
        parse_mode="HTML",
    )


# ── Ответ пользователю ────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm:reply:"))
async def reply_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    uid = int(query.data.rsplit(":", 1)[1])
    await state.set_state(AdminStates.reply_to_user)
    await state.update_data(target_uid=uid)
    await query.message.answer(
        f"✏️ <b>Режим ответа</b>\n\nНапишите сообщение для пользователя <code>{uid}</code>.\n\n"
        f"/cancel — отменить.",
        parse_mode="HTML",
    )


@router.message(AdminStates.reply_to_user, F.text, ~F.text.startswith("/"))
async def reply_send(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    uid = data["target_uid"]
    try:
        await message.bot.send_message(
            uid,
            f"💬 <b>Ответ поддержки:</b>\n\n{message.text}",
            parse_mode="HTML",
        )
        await message.answer(f"✅ Отправлено пользователю <code>{uid}</code>", parse_mode="HTML")
    except Exception as exc:
        await message.answer(f"❌ Ошибка: {exc}")


# ── Выдача PocketOption ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("adm:pocket:"))
async def pocket_start(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    uid = int(query.data.rsplit(":", 1)[1])
    await state.set_state(AdminStates.pocket_for_user)
    await state.update_data(target_uid=uid)
    await query.message.answer(
        f"📦 <b>Выдача PocketOption</b> пользователю <code>{uid}</code>\n\n"
        f"Напишите данные аккаунта (логин, пароль, ссылка).\n\n/cancel — отменить.",
        parse_mode="HTML",
    )


@router.message(AdminStates.pocket_for_user, F.text, ~F.text.startswith("/"))
async def pocket_send(message: Message, state: FSMContext, session) -> None:
    data = await state.get_data()
    await state.clear()
    uid = data["target_uid"]
    try:
        await message.bot.send_message(
            uid,
            f"🏦 <b>Ваш аккаунт PocketOption готов!</b>\n\n{message.text}",
            parse_mode="HTML",
        )
    except Exception as exc:
        await message.answer(f"❌ Ошибка отправки: {exc}")
        return

    # помечаем последнюю открытую заявку выданной
    orders = await repo.list_pocket_orders(session, status="new")
    for order, _user in orders:
        if order.user_id == uid:
            await repo.fulfill_pocket_order(session, order)
            break
    await message.answer(f"✅ Данные PocketOption отправлены пользователю <code>{uid}</code>", parse_mode="HTML")


# ── Ответ реплаем на пересланное сообщение поддержки ─────────────────────────

@router.message(F.reply_to_message, F.text)
async def reply_to_forwarded(message: Message, session) -> None:
    uid = await repo.user_by_forwarded_msg(session, message.reply_to_message.message_id)
    if not uid:
        return
    try:
        await message.bot.send_message(
            uid,
            f"💬 <b>Ответ поддержки:</b>\n\n{message.text}",
            parse_mode="HTML",
        )
        await message.answer("✅ Ответ отправлен.")
    except Exception as exc:
        await message.answer(f"❌ Ошибка: {exc}")
