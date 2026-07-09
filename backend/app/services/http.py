"""Общая aiohttp-сессия для всего процесса."""
from __future__ import annotations

import aiohttp

_session: aiohttp.ClientSession | None = None


def get_http_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        connector = aiohttp.TCPConnector(limit=20, ttl_dns_cache=300)
        _session = aiohttp.ClientSession(connector=connector)
    return _session


async def close_http_session() -> None:
    global _session
    if _session and not _session.closed:
        await _session.close()
    _session = None
