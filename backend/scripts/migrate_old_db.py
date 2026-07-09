#!/usr/bin/env python3
"""Перенос данных из старой SQLite-базы (bot_database.db) в новую схему.

Запуск:  python scripts/migrate_old_db.py /path/to/bot_database.db
Повторный запуск безопасен: существующие пользователи не дублируются.
"""
from __future__ import annotations

import asyncio
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.db.models import Purchase, SupportMessage, User  # noqa: E402
from app.db.session import get_sessionmaker, init_db  # noqa: E402


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def migrate(old_db_path: str) -> None:
    old = sqlite3.connect(old_db_path)
    old.row_factory = sqlite3.Row

    await init_db()
    async with get_sessionmaker()() as session:
        existing_ids = set((await session.execute(select(User.id))).scalars())

        users = old.execute("SELECT * FROM users").fetchall()
        added_users = 0
        for row in users:
            if row["user_id"] in existing_ids:
                continue
            session.add(User(
                id=row["user_id"],
                username=row["username"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                language=row["language"] or "ru",
                is_vip=bool(row["is_vip"]),
                created_at=_parse_dt(row["joined_at"]) or datetime.utcnow(),
            ))
            added_users += 1

        purchase_count = (await session.execute(select(Purchase.id))).scalars().first()
        added_purchases = 0
        if purchase_count is None:  # переносим покупки только в пустую таблицу
            for row in old.execute("SELECT * FROM purchases").fetchall():
                plan = row["plan"] or ""
                session.add(Purchase(
                    user_id=row["user_id"],
                    product_type="pocket" if "Pocket" in plan else "vip",
                    plan_name=plan,
                    amount_usd=float(row["amount"] or 0),
                    created_at=_parse_dt(row["created_at"]) or datetime.utcnow(),
                ))
                added_purchases += 1

            for row in old.execute("SELECT * FROM support_messages").fetchall():
                session.add(SupportMessage(
                    user_id=row["user_id"],
                    forwarded_msg_id=row["forwarded_msg_id"],
                    created_at=_parse_dt(row["created_at"]) or datetime.utcnow(),
                ))

        await session.commit()

    old.close()
    print(f"Готово: перенесено пользователей {added_users}, покупок {added_purchases}.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Использование: python scripts/migrate_old_db.py /path/to/bot_database.db")
    asyncio.run(migrate(sys.argv[1]))
