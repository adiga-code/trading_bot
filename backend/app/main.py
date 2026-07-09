"""Точка входа: FastAPI (API + статика Mini App) и aiogram-бот в одном процессе."""
from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import runtime
from app.api import admin as admin_api
from app.api import market as market_api
from app.api import payments as payments_api
from app.bot.setup import create_bot, create_dispatcher, on_startup
from app.config import get_settings
from app.db.session import init_db
from app.payments.watcher import watcher_loop
from app.services.http import close_http_session
from app.services.subscriptions import scheduler_loop

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
# токен бота не должен светиться в логах запросов
logging.getLogger("aiogram.event").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_db()

    background: list[asyncio.Task] = []
    polling_task: asyncio.Task | None = None

    if settings.bot_token:
        runtime.bot = create_bot()
        dp = create_dispatcher()
        await on_startup(runtime.bot)
        polling_task = asyncio.create_task(
            dp.start_polling(runtime.bot, drop_pending_updates=True, handle_signals=False)
        )
        background.append(asyncio.create_task(watcher_loop(runtime.bot)))
        background.append(asyncio.create_task(scheduler_loop(runtime.bot)))
        logger.info("Bot polling + watchers started")
    else:
        logger.warning("BOT_TOKEN не задан — работает только API/статика")

    yield

    for task in background:
        task.cancel()
    if polling_task:
        polling_task.cancel()
    if runtime.bot:
        await runtime.bot.session.close()
    await close_http_session()


app = FastAPI(title="Forex Trd'K", lifespan=lifespan, docs_url=None, redoc_url=None)

app.include_router(market_api.router)
app.include_router(payments_api.router)
app.include_router(admin_api.router)


# ── Статика Mini App (собранный фронтенд) ────────────────────────────────────
_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", get_settings().frontend_dist))

if os.path.isdir(_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(_dist, "assets")), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        file_path = os.path.join(_dist, path)
        if path and os.path.isfile(file_path):
            return FileResponse(file_path)
        index = os.path.join(_dist, "index.html")
        return FileResponse(index, headers={"Cache-Control": "no-store, max-age=0"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=get_settings().port)
