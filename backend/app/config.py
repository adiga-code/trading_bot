"""Настройки приложения. Все секреты приходят из окружения (.env) — в коде их нет."""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    bot_token: str = ""
    admin_ids: list[int] = []
    vip_channel_id: int | None = None  # id канала (-100...), куда бот выдаёт доступ
    mini_app_url: str = ""

    @field_validator("vip_channel_id", mode="before")
    @classmethod
    def _empty_channel_id_is_none(cls, v):
        if v == "" or v is None:
            return None
        return int(v) if isinstance(v, str) else v

    # Платёжные шлюзы
    gate2328_api_key: str = ""
    gate2328_project_id: str = ""
    gate2328_base_url: str = "https://api.2328.io/api/v1"
    payment_callback_url: str = ""

    # CryptoBot (@CryptoBot Crypto Pay API) — токен приложения из Crypto Pay → My Apps
    cryptobot_api_token: str = ""
    cryptobot_base_url: str = "https://pay.crypt.bot/api"

    # NicePay (nicepay.io) — СБП. merchant_id/secret из настроек мерчанта.
    nicepay_merchant_id: str = ""
    nicepay_secret_key: str = ""
    nicepay_base_url: str = "https://nicepay.io/public/api"
    # Курс USD→RUB для конвертации тарифов (СБП принимает только рубли).
    # 0 = не настроен — создание счёта тогда будет падать с понятной ошибкой.
    nicepay_usd_rub_rate: float = 0.0

    # Инфраструктура
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"
    port: int = 8080
    frontend_dist: str = "../frontend/dist"

    # Ссылки
    privacy_url: str = "https://telegra.ph/Politika-konfidencialnosti-06-21-31"
    terms_url: str = "https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19"
    support_username: str = "forextrdk"

    brand_name: str = "Forex Trd'K"

    # Автовыдача VIP
    subscription_check_interval: int = 3600     # сек между проверками истёкших подписок
    subscription_remind_before_days: int = 3    # за сколько дней напоминать о продлении

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


@lru_cache
def get_settings() -> Settings:
    return Settings()
