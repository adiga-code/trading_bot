"""Скрипт миграции переносит юзеров и покупки из старой схемы."""
import sqlite3

from sqlalchemy import select

from app.db import repo
from app.db.models import Purchase
from scripts.migrate_old_db import migrate


def _make_old_db(path: str) -> None:
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,"
              " last_name TEXT, language TEXT DEFAULT 'en', joined_at TEXT, is_vip INTEGER DEFAULT 0)")
    c.execute("CREATE TABLE purchases (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,"
              " plan TEXT, amount REAL, created_at TEXT)")
    c.execute("CREATE TABLE support_messages (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,"
              " forwarded_msg_id INTEGER, created_at TEXT)")
    c.execute("INSERT INTO users VALUES (10, 'alice', 'Alice', NULL, 'ru', '2026-01-01T10:00:00', 1)")
    c.execute("INSERT INTO users VALUES (20, NULL, 'Bob', 'B', 'en', '2026-02-02T10:00:00', 0)")
    c.execute("INSERT INTO purchases (user_id, plan, amount, created_at)"
              " VALUES (10, 'VIP 1 Месяц', 45, '2026-01-05T10:00:00')")
    c.execute("INSERT INTO purchases (user_id, plan, amount, created_at)"
              " VALUES (20, 'PocketOption 65$', 65, '2026-02-05T10:00:00')")
    conn.commit()
    conn.close()


async def test_migrate_old_db(db, tmp_path):
    old_path = str(tmp_path / "old.db")
    _make_old_db(old_path)

    await migrate(old_path)

    alice = await repo.get_user(db, 10)
    assert alice is not None and alice.is_vip and alice.username == "alice"
    assert await repo.count_users(db) == 2

    purchases = (await db.execute(select(Purchase))).scalars().all()
    assert len(purchases) == 2
    types = {p.user_id: p.product_type for p in purchases}
    assert types == {10: "vip", 20: "pocket"}

    # повторный запуск не дублирует
    await migrate(old_path)
    assert await repo.count_users(db) == 2
