from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User as TgUser

from app.db import repo
from app.db.session import get_sessionmaker


class DbMiddleware(BaseMiddleware):
    """Открывает сессию БД на каждый апдейт и апсертит пользователя."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async with get_sessionmaker()() as session:
            data["session"] = session
            tg_user: TgUser | None = data.get("event_from_user")
            if tg_user and not tg_user.is_bot:
                data["db_user"] = await repo.upsert_user(
                    session, tg_user.id, tg_user.username, tg_user.first_name, tg_user.last_name
                )
            return await handler(event, data)
