# ── Стадия 1: сборка фронтенда ───────────────────────────────────────────────
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ── Стадия 2: python-приложение ──────────────────────────────────────────────
FROM python:3.12-slim
WORKDIR /app

COPY backend/pyproject.toml ./backend/
RUN pip install --no-cache-dir ./backend

COPY backend/ ./backend/
COPY --from=frontend /build/dist ./frontend/dist

WORKDIR /app/backend
ENV FRONTEND_DIST=../frontend/dist \
    DATABASE_URL=sqlite+aiosqlite:////data/bot.db

VOLUME /data
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
