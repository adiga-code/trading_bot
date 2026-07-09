"""Глобальные объекты процесса (инициализируются в lifespan)."""
from __future__ import annotations

from aiogram import Bot

bot: Bot | None = None


def get_bot() -> Bot:
    if bot is None:
        raise RuntimeError("Bot is not initialized (BOT_TOKEN не задан?)")
    return bot
