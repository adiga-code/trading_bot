"""API веб-админки. Каждый запрос проверяет initData и членство в ADMIN_IDS."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app import runtime
from app.api.auth import WebAppUser, current_admin
from app.api.deps import db_session
from app.db import repo
from app.db.models import utcnow
from app.plans import VIP_PLANS
from app.services import subscriptions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(current_admin)])


def _user_out(u) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "display_name": u.display_name,
        "is_vip": u.is_vip,
        "created_at": u.created_at.isoformat(),
    }


@router.get("/stats")
async def stats(session: AsyncSession = Depends(db_session)):
    now = utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    total_users = await repo.count_users(session)
    users_7d = await repo.count_users(session, since=week_ago)
    users_30d = await repo.count_users(session, since=month_ago)
    vip_count = await repo.count_vip_users(session)
    total_count, total_revenue = await repo.purchases_stats(session)
    count_7d, revenue_7d = await repo.purchases_stats(session, since=week_ago)
    count_30d, revenue_30d = await repo.purchases_stats(session, since=month_ago)
    new_pocket = await repo.list_pocket_orders(session, status="new")

    return {
        "users": {"total": total_users, "last7d": users_7d, "last30d": users_30d, "vip": vip_count},
        "purchases": {
            "total": total_count,
            "revenue_total": total_revenue,
            "last7d": count_7d,
            "revenue_7d": revenue_7d,
            "last30d": count_30d,
            "revenue_30d": revenue_30d,
        },
        "pocket_orders_new": len(new_pocket),
    }


@router.get("/users")
async def users(
    search: str = "",
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(db_session),
):
    items = await repo.list_users(session, search=search, limit=min(limit, 200), offset=offset)
    return {"items": [_user_out(u) for u in items]}


@router.get("/users/{user_id}")
async def user_detail(user_id: int, session: AsyncSession = Depends(db_session)):
    """Карточка пользователя: профиль + подписка + последние покупки."""
    user = await repo.get_user(session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    sub = await repo.latest_subscription(session, user_id)
    plan = VIP_PLANS.get(sub.plan_key) if sub else None
    subscription = None
    if sub:
        subscription = {
            "plan_key": sub.plan_key,
            "plan_name": plan.name if plan else sub.plan_key,
            "status": sub.status,
            "started_at": sub.started_at.isoformat(),
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        }

    purchases = await repo.user_purchases(session, user_id)
    return {
        **_user_out(user),
        "subscription": subscription,
        "purchases": [
            {
                "id": p.id,
                "product_type": p.product_type,
                "plan_name": p.plan_name,
                "amount_usd": p.amount_usd,
                "created_at": p.created_at.isoformat(),
            }
            for p in purchases
        ],
    }


@router.get("/vip-users")
async def vip_users(session: AsyncSession = Depends(db_session)):
    rows = await repo.list_vip_users(session)
    out = []
    for u, sub in rows:
        plan = VIP_PLANS.get(sub.plan_key)
        out.append({
            **_user_out(u),
            "plan_key": sub.plan_key,
            "plan_name": plan.name if plan else sub.plan_key,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        })
    return {"items": out}


@router.get("/purchases")
async def purchases(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(db_session)):
    rows = await repo.list_purchases(session, limit=min(limit, 200), offset=offset)
    return {"items": [
        {
            "id": p.id,
            "user_id": p.user_id,
            "user": u.display_name if u else f"ID:{p.user_id}",
            "product_type": p.product_type,
            "plan_name": p.plan_name,
            "amount_usd": p.amount_usd,
            "created_at": p.created_at.isoformat(),
        }
        for p, u in rows
    ]}


@router.get("/payments")
async def payments(limit: int = 100, offset: int = 0, session: AsyncSession = Depends(db_session)):
    items = await repo.list_payments(session, limit=min(limit, 200), offset=offset)
    return {"items": [
        {
            "id": p.id,
            "user_id": p.user_id,
            "gateway": p.gateway,
            "plan_name": p.plan_name,
            "amount_usd": p.amount_usd,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
        }
        for p in items
    ]}


@router.get("/pocket-orders")
async def pocket_orders(status: str | None = None, session: AsyncSession = Depends(db_session)):
    rows = await repo.list_pocket_orders(session, status=status)
    return {"items": [
        {
            "id": o.id,
            "user_id": o.user_id,
            "user": u.display_name if u else f"ID:{o.user_id}",
            "tier_index": o.tier_index,
            "amount_usd": o.amount_usd,
            "balance_usd": o.balance_usd,
            "status": o.status,
            "created_at": o.created_at.isoformat(),
            "fulfilled_at": o.fulfilled_at.isoformat() if o.fulfilled_at else None,
        }
        for o, u in rows
    ]}


class FulfillRequest(BaseModel):
    text: str


@router.post("/pocket-orders/{order_id}/fulfill")
async def fulfill_order(order_id: int, body: FulfillRequest, session: AsyncSession = Depends(db_session)):
    rows = await repo.list_pocket_orders(session)
    order = next((o for o, _u in rows if o.id == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    bot = runtime.get_bot()
    try:
        await bot.send_message(
            order.user_id,
            f"🏦 <b>Ваш аккаунт PocketOption готов!</b>\n\n{body.text}",
            parse_mode="HTML",
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Не удалось отправить сообщение: {exc}")
    await repo.fulfill_pocket_order(session, order)
    return {"ok": True}


class VipGrantRequest(BaseModel):
    plan_key: str


@router.post("/users/{user_id}/vip")
async def grant_vip(user_id: int, body: VipGrantRequest, session: AsyncSession = Depends(db_session)):
    if body.plan_key not in VIP_PLANS:
        raise HTTPException(status_code=400, detail="Unknown plan")
    bot = runtime.get_bot()
    sub = await subscriptions.grant_vip(bot, session, user_id, body.plan_key)
    return {"ok": True, "expires_at": sub.expires_at.isoformat() if sub.expires_at else None}


@router.delete("/users/{user_id}/vip")
async def revoke_vip(user_id: int, session: AsyncSession = Depends(db_session)):
    sub = await repo.active_subscription(session, user_id)
    if sub:
        await subscriptions.revoke_vip(runtime.get_bot(), session, sub, notify=False)
    else:
        await repo.set_vip(session, user_id, False)
    return {"ok": True}


class MessageRequest(BaseModel):
    text: str


@router.post("/users/{user_id}/message")
async def message_user(user_id: int, body: MessageRequest):
    bot = runtime.get_bot()
    try:
        await bot.send_message(user_id, f"💬 <b>Сообщение от Forex Trd'K:</b>\n\n{body.text}", parse_mode="HTML")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Не удалось отправить: {exc}")
    return {"ok": True}


class BroadcastRequest(BaseModel):
    text: str


@router.post("/broadcast")
async def broadcast(body: BroadcastRequest, session: AsyncSession = Depends(db_session)):
    """Рассылка всем пользователям. Шлём в фоне, не блокируя ответ."""
    users = await repo.list_users(session, limit=100000)
    bot = runtime.get_bot()

    async def _send_all(user_ids: list[int], text: str) -> None:
        sent = 0
        for uid in user_ids:
            try:
                await bot.send_message(uid, text, parse_mode="HTML")
                sent += 1
            except Exception:
                pass
            await asyncio.sleep(0.05)  # ~20 msg/s — лимит Telegram ~30/s
        logger.info("broadcast finished: %s/%s", sent, len(user_ids))

    asyncio.create_task(_send_all([u.id for u in users], body.text))
    return {"ok": True, "recipients": len(users)}
