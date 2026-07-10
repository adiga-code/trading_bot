from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    username: Mapped[str | None] = mapped_column(String(64))
    first_name: Mapped[str | None] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(128))
    language: Mapped[str] = mapped_column(String(8), default="ru")
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def display_name(self) -> str:
        if self.username:
            return f"@{self.username}"
        parts = [p for p in (self.first_name, self.last_name) if p]
        return " ".join(parts) or f"ID:{self.id}"


class PaymentStatus:
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class Payment(Base):
    """Счёт в платёжном шлюзе. Статус хранится в БД, поэтому проверка оплат
    переживает рестарт процесса (в старой версии поллинг жил только в памяти)."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    gateway: Mapped[str] = mapped_column(String(16))          # gate2328 | stars
    external_id: Mapped[str] = mapped_column(String(128), index=True)
    product_type: Mapped[str] = mapped_column(String(8))      # vip | pocket
    plan_key: Mapped[str] = mapped_column(String(16))
    plan_name: Mapped[str] = mapped_column(String(128))
    amount_usd: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default=PaymentStatus.PENDING, index=True)
    pay_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Purchase(Base):
    """Подтверждённая покупка (после оплаты либо после ручной выдачи)."""

    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    payment_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("payments.id"))
    product_type: Mapped[str] = mapped_column(String(8))
    plan_key: Mapped[str] = mapped_column(String(16), default="")
    plan_name: Mapped[str] = mapped_column(String(128))
    amount_usd: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SubscriptionStatus:
    ACTIVE = "active"
    EXPIRED = "expired"


class Subscription(Base):
    """VIP-подписка: срок хранится в БД, доступ в канал выдаёт/забирает админ вручную."""

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    plan_key: Mapped[str] = mapped_column(String(16))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)  # None = навсегда
    status: Mapped[str] = mapped_column(String(16), default=SubscriptionStatus.ACTIVE, index=True)
    invite_link: Mapped[str | None] = mapped_column(Text)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)


class PocketOrderStatus:
    NEW = "new"
    FULFILLED = "fulfilled"


class PocketOrder(Base):
    """Оплаченная заявка на аккаунт PocketOption — выдаётся вручную через админку."""

    __tablename__ = "pocket_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    payment_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("payments.id"))
    tier_index: Mapped[int] = mapped_column(Integer)
    amount_usd: Mapped[float] = mapped_column(Float)
    balance_usd: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default=PocketOrderStatus.NEW, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime)


class SupportMessage(Base):
    __tablename__ = "support_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    forwarded_msg_id: Mapped[int] = mapped_column(BigInteger, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
