"""Публичные эндпоинты: здоровье, конфиг тарифов, рыночные данные."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import WebAppUser, current_user
from app.api.deps import db_session
from app.config import get_settings
from app.db import repo
from app.plans import CRYPTO_OPTIONS, POCKET_TIERS, TRADING_PAIRS, VIP_PLANS
from app.services import market

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/health")
async def health():
    return {"ok": True}


@router.get("/config")
async def app_config():
    """Тарифы и справочники для фронтенда — единый источник цен."""
    s = get_settings()
    return {
        "vip_plans": [
            {
                "key": p.key,
                "name": p.name,
                "months": p.months,
                "price_usd": p.price_usd,
                "old_price_usd": p.old_price_usd,
                "stars": p.stars,
            }
            for p in VIP_PLANS.values()
        ],
        "pocket_tiers": [
            {
                "index": t.index,
                "pay_usd": t.pay_usd,
                "balance_usd": t.balance_usd,
                "stars": t.stars,
                "name": t.name,
            }
            for t in POCKET_TIERS
        ],
        "crypto_options": [
            {"label": label, "cur": cur, "net": net} for label, cur, net in CRYPTO_OPTIONS
        ],
        "trading_pairs": TRADING_PAIRS,
        "support_username": s.support_username,
        "privacy_url": s.privacy_url,
        "terms_url": s.terms_url,
    }


@router.get("/me")
async def me(
    user: WebAppUser = Depends(current_user),
    session: AsyncSession = Depends(db_session),
):
    db_user = await repo.upsert_user(session, user.id, user.username, user.first_name, user.last_name)
    sub = await repo.active_subscription(session, user.id)
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "is_vip": db_user.is_vip,
        "vip_expires_at": sub.expires_at.isoformat() if sub and sub.expires_at else None,
    }


@router.get("/metals")
async def metals():
    return await market.metals_spot()


@router.get("/metalchart")
async def metalchart(
    symbol: str = Query(default="SI=F", max_length=12),
    tf: str = Query(default="1h", max_length=4),
):
    return await market.metal_chart(symbol, tf)
