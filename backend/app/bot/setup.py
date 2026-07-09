from __future__ import annotations

import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.bot.middlewares import DbMiddleware
from app.bot.routers import build_root_router
from app.config import get_settings

logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    return Bot(
        token=get_settings().bot_token,
        default=DefaultBotProperties(parse_mode=None),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbMiddleware())
    dp.include_router(build_root_router())
    return dp


async def on_startup(bot: Bot) -> None:
    settings = get_settings()
    if settings.mini_app_url:
        try:
            await bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="Mini App", web_app=WebAppInfo(url=settings.mini_app_url))
            )
        except Exception as exc:
            logger.warning("set_chat_menu_button: %s", exc)
