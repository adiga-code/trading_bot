from __future__ import annotations

import os

import pytest
import pytest_asyncio

os.environ.setdefault("BOT_TOKEN", "12345:TEST_TOKEN")
os.environ.setdefault("ADMIN_IDS", "[1]")

from app.config import get_settings  # noqa: E402
from app.db import session as db_session  # noqa: E402


@pytest_asyncio.fixture
async def db(tmp_path, monkeypatch):
    """Свежая файловая SQLite на каждый тест."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/test.db")
    get_settings.cache_clear()
    db_session.reset_engine()
    await db_session.init_db()
    async with db_session.get_sessionmaker()() as session:
        yield session
    db_session.reset_engine()
    get_settings.cache_clear()


class FakeBot:
    """Мини-заглушка aiogram.Bot: записывает исходящие вызовы."""

    def __init__(self):
        self.messages: list[tuple[int, str]] = []
        self.invites: list[int] = []
        self.banned: list[int] = []
        self.unbanned: list[int] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append((chat_id, text))

    async def create_chat_invite_link(self, chat_id, **kwargs):
        self.invites.append(chat_id)

        class _Invite:
            invite_link = "https://t.me/+test_invite"

        return _Invite()

    async def ban_chat_member(self, chat_id, user_id):
        self.banned.append(user_id)

    async def unban_chat_member(self, chat_id, user_id):
        self.unbanned.append(user_id)


@pytest.fixture
def fake_bot():
    return FakeBot()
