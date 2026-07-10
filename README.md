# Forex Trd'K — Telegram-бот + Mini App

Продажа VIP-подписок на сигналы и аккаунтов PocketOption: бот на **aiogram 3**,
API на **FastAPI**, Mini App на **React + Vite + TypeScript + Tailwind**.
Один процесс, один деплой: FastAPI отдаёт API и собранный фронтенд, бот работает
внутри него (polling).

## Возможности

- 💎 **VIP-подписки** (1/3/6 мес, lifetime): после оплаты админ получает карточку
  покупателя (имя, @username, ID, тариф, цена) с кнопкой «Написать» и выдаёт доступ
  в канал вручную; срок хранится в БД, об истечении бот уведомляет админа
- 🏦 **PocketOption-заявки** — оплата автоматом, выдача аккаунта вручную из админки
- 💳 Оплата: крипта через **2328.io** и **Telegram Stars**
- 📈 Mini App: живые цены Binance + золото/серебро, свечные графики, оплата в 2 тапа
- 👑 **Веб-админка** внутри Mini App (только для ADMIN_IDS): дашборд с выручкой,
  пользователи, покупки/счета, PocketOption-заявки, рассылка
- 🔐 Все запросы Mini App проверяются по подписи Telegram initData
- 💾 Статусы платежей в БД — проверка оплат переживает рестарты

## Структура

```
backend/
  app/
    main.py          # FastAPI + бот в одном процессе
    config.py        # настройки из env (секретов в коде нет)
    plans.py         # ЕДИНСТВЕННОЕ место с ценами
    db/              # SQLAlchemy 2.0 async: модели, сессии, запросы
    bot/             # aiogram 3: роутеры, клавиатуры, middleware
    payments/        # шлюз 2328.io + watcher статусов
    api/             # auth (initData), payments, market, admin
    services/        # подписки, fulfillment, рынок
  scripts/migrate_old_db.py  # перенос данных из старой bot_database.db
  tests/
frontend/            # Mini App: React + Vite + TS + Tailwind
```

## Быстрый старт (локально)

```bash
# 1. Бэкенд
cd backend
pip install -e ".[dev]"
cp ../.env.example .env        # заполни BOT_TOKEN и остальное
uvicorn app.main:app --port 8080

# 2. Фронтенд (отдельный терминал, hot-reload, /api проксируется на :8080)
cd frontend
npm install
npm run dev
```

Продакшен-сборка фронта: `npm run build` → `frontend/dist`, FastAPI отдаст её сам.

Тесты: `cd backend && pytest`

## Docker

```bash
cp .env.example .env   # заполнить
docker compose up --build
```

## Деплой на Railway

1. Подключи репозиторий — Railway соберёт по `Dockerfile` (см. `railway.json`)
2. Добавь **Volume** и примонтируй в `/data` (там живёт SQLite)
3. Пропиши переменные окружения из `.env.example`
4. Сгенерируй домен и укажи его в `MINI_APP_URL` (`https://<домен>`)
5. В @BotFather: Bot Settings → Menu Button → укажи тот же URL

## ⚠️ Перед запуском: перевыпусти секреты

Старые ключи лежали в коде и в git — считай их украденными:

| Секрет | Где перевыпустить |
|---|---|
| `BOT_TOKEN` | @BotFather → /revoke |
| `GATE2328_API_KEY` | кабинет 2328.io |

## Выдача VIP

После оплаты бот присылает админу карточку покупателя с кнопкой «✉️ Написать» —
доступ в VIP-канал выдаётся вручную. Срок подписки хранится в БД: за 3 дня до
конца и при истечении бот уведомляет админа, чтобы тот убрал пользователя из
канала.

## Перенос данных со старого бота

```bash
cd backend
python scripts/migrate_old_db.py /path/to/bot_database.db
```
