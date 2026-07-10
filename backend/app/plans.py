"""Тарифы и справочники — единственное место, где заданы цены.

Бот, API и фронтенд (через /api/config) берут данные отсюда,
поэтому цены не могут разъехаться между поверхностями.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VipPlan:
    key: str
    name: str          # человекочитаемое название
    months: int | None  # None = навсегда
    price_usd: float
    old_price_usd: float
    stars: int         # цена в Telegram Stars


VIP_PLANS: dict[str, VipPlan] = {
    "1month":   VipPlan("1month",   "VIP 1 Месяц",   1,    45.0,  200.0,  2000),
    "3months":  VipPlan("3months",  "VIP 3 Месяца",  3,    119.0, 300.0,  6000),
    "6months":  VipPlan("6months",  "VIP 6 Месяцев", 6,    159.0, 500.0,  8000),
    "lifetime": VipPlan("lifetime", "VIP Навсегда",  None, 199.0, 1000.0, 10000),
}


@dataclass(frozen=True)
class PocketTier:
    index: int
    pay_usd: float      # сколько платит клиент
    balance_usd: float  # баланс выдаваемого аккаунта
    stars: int

    @property
    def key(self) -> str:
        return str(self.index)

    @property
    def name(self) -> str:
        return f"PocketOption {self.pay_usd:.0f}$→{self.balance_usd:.0f}$"


POCKET_TIERS: list[PocketTier] = [
    PocketTier(0, 65.0,  87.0,  5000),
    PocketTier(1, 120.0, 175.0, 9000),
    PocketTier(2, 230.0, 350.0, 18000),
]


def resolve_plan(product_type: str, plan_key: str) -> tuple[str, float] | None:
    """Название и цена в USD по типу продукта и ключу тарифа; None если тариф неизвестен."""
    if product_type == "vip":
        plan = VIP_PLANS.get(plan_key)
        return (plan.name, plan.price_usd) if plan else None
    if product_type == "pocket":
        try:
            tier = POCKET_TIERS[int(plan_key)]
        except (ValueError, IndexError):
            return None
        return (tier.name, tier.pay_usd)
    return None


def resolve_stars(product_type: str, plan_key: str) -> tuple[str, int, str] | None:
    """(название, цена в Stars, invoice payload) для оплаты звёздами."""
    if product_type == "vip":
        plan = VIP_PLANS.get(plan_key)
        if not plan:
            return None
        return plan.name, plan.stars, f"vip_{plan.key}"
    if product_type == "pocket":
        try:
            tier = POCKET_TIERS[int(plan_key)]
        except (ValueError, IndexError):
            return None
        return tier.name, tier.stars, f"pocket_{tier.index}"
    return None


# (подпись, валюта, сеть) — криптовалюты, которые принимает 2328.io
CRYPTO_OPTIONS: list[tuple[str, str, str]] = [
    ("₿ BTC",          "BTC",   "BTC"),
    ("⟠ ETH",          "ETH",   "ETH-ERC20"),
    ("₮ USDT (TRC20)", "USDT",  "TRX-TRC20"),
    ("₮ USDT (ERC20)", "USDT",  "ETH-ERC20"),
    ("₮ USDT (BEP20)", "USDT",  "BSC-BEP20"),
    ("◈ USDC",         "USDC",  "ETH-ERC20"),
    ("◎ SOL",          "SOL",   "SOL"),
    ("💎 TON",         "TON",   "TON"),
    ("⬡ BNB",          "BNB",   "BSC-BEP20"),
    ("Ⓜ MATIC",        "MATIC", "MATIC"),
    ("TRX",            "TRX",   "TRX-TRC20"),
    ("∞ XMR",          "XMR",   "XMR"),
]

TRADING_PAIRS: list[str] = [
    "ADAUSDT", "ALGOUSDT", "RUNEUSDT", "HYPEUSDT", "XRPUSDT",
    "APEUSDT", "HBARUSDT", "RENDERUSDT", "DUSKUSDT", "TWTUSDT",
    "SUIUSDT", "BNBUSDT", "ETHUSDT", "GMTUSDT", "ORDIUSDT",
    "UNIUSDT", "SOLUSDT", "CRVUSDT", "GMXUSDT", "IDUSDT",
    "FILUSDT", "STGUSDT", "IOTAUSDT", "ENAUSDT", "APTUSDT",
    "NEARUSDT", "IOUSDT", "WUSDT", "TNSRUSDT", "TIAUSDT",
    "SUPERUSDT",
]
