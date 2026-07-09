"""Рыночные данные: Binance (крипта), gold-api.com (спот металлов), Yahoo (свечи металлов).

Все ответы кэшируются на короткое время, чтобы не упираться в лимиты внешних API.
"""
from __future__ import annotations

import logging
import time

import aiohttp

from app.services.http import get_http_session

logger = logging.getLogger(__name__)

_METALS_CACHE: dict = {"ts": 0.0, "data": None}
_CHART_CACHE: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 30  # сек

# таймфрейм → (interval, range) для Yahoo Finance
YF_TIMEFRAMES = {
    "5m": ("5m", "5d"),
    "15m": ("15m", "1mo"),
    "1h": ("60m", "3mo"),
    "4h": ("60m", "6mo"),  # агрегируется в 4h ниже
    "1d": ("1d", "2y"),
    "1w": ("1wk", "10y"),
}


async def binance_24h_changes(pairs: list[str]) -> dict[str, float]:
    """Процент изменения за 24ч по списку пар."""
    wanted = set(pairs)
    out: dict[str, float] = {}
    try:
        async with get_http_session().get(
            "https://api.binance.com/api/v3/ticker/24hr",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            if resp.status == 200:
                for item in await resp.json():
                    sym = item.get("symbol", "")
                    if sym in wanted:
                        out[sym] = float(item.get("priceChangePercent", 0))
    except Exception as exc:
        logger.warning("binance_24h_changes: %s", exc)
    return out


async def metals_spot() -> dict:
    """Спот-цены золота и серебра, кэш 30 сек."""
    now = time.time()
    if _METALS_CACHE["data"] and now - _METALS_CACHE["ts"] < CACHE_TTL:
        return _METALS_CACHE["data"]
    out: dict = {}
    for key, sym in (("gold", "XAU"), ("silver", "XAG")):
        try:
            async with get_http_session().get(
                f"https://api.gold-api.com/price/{sym}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                j = await resp.json()
                out[key] = {"price": j.get("price")}
        except Exception as exc:
            logger.warning("metals %s: %s", sym, exc)
            out[key] = {"price": None}
    _METALS_CACHE["ts"] = now
    _METALS_CACHE["data"] = out
    return out


def _aggregate(candles: list[dict], bucket_sec: int) -> list[dict]:
    buckets: dict[int, dict] = {}
    order: list[int] = []
    for c in candles:
        k = c["time"] - (c["time"] % bucket_sec)
        b = buckets.get(k)
        if b is None:
            buckets[k] = {"time": k, "open": c["open"], "high": c["high"],
                          "low": c["low"], "close": c["close"]}
            order.append(k)
        else:
            b["high"] = max(b["high"], c["high"])
            b["low"] = min(b["low"], c["low"])
            b["close"] = c["close"]
    return [buckets[k] for k in order]


async def metal_chart(symbol: str, tf: str) -> dict:
    """Свечи по металлу через Yahoo Finance, кэш 30 сек."""
    interval, rng = YF_TIMEFRAMES.get(tf, ("60m", "3mo"))
    cache_key = f"{symbol}|{tf}"
    now = time.time()
    cached = _CHART_CACHE.get(cache_key)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]
    try:
        async with get_http_session().get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
            params={"interval": interval, "range": rng},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=aiohttp.ClientTimeout(total=12),
        ) as resp:
            d = await resp.json()
        res = d["chart"]["result"][0]
        ts = res["timestamp"]
        q = res["indicators"]["quote"][0]
        candles = []
        for i, t in enumerate(ts):
            o, h, l, c = q["open"][i], q["high"][i], q["low"][i], q["close"][i]
            if None in (o, h, l, c):
                continue
            candles.append({"time": int(t), "open": o, "high": h, "low": l, "close": c})
        if tf == "4h":
            candles = _aggregate(candles, 4 * 3600)
        out = {"candles": candles, "price": res.get("meta", {}).get("regularMarketPrice")}
        _CHART_CACHE[cache_key] = (now, out)
        return out
    except Exception as exc:
        logger.warning("metal_chart %s: %s", symbol, exc)
        return {"candles": [], "error": "chart unavailable"}
