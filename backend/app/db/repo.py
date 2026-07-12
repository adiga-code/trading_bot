"""Запросы к БД. Все функции принимают активную AsyncSession."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Payment,
    PaymentStatus,
    PocketOrder,
    PocketOrderStatus,
    Purchase,
    Subscription,
    SubscriptionStatus,
    User,
    utcnow,
)


# ── Пользователи ──────────────────────────────────────────────────────────────

async def upsert_user(
    session: AsyncSession,
    user_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        user = User(id=user_id, username=username, first_name=first_name, last_name=last_name)
        session.add(user)
    else:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
    await session.commit()
    return user


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    return await session.get(User, user_id)


async def set_language(session: AsyncSession, user_id: int, language: str) -> None:
    user = await session.get(User, user_id)
    if user:
        user.language = language
        await session.commit()


async def set_vip(session: AsyncSession, user_id: int, status: bool) -> None:
    user = await session.get(User, user_id)
    if user:
        user.is_vip = status
        await session.commit()


async def list_users(session: AsyncSession, search: str = "", limit: int = 200, offset: int = 0) -> list[User]:
    q = select(User).order_by(User.created_at.desc())
    if search:
        like = f"%{search}%"
        q = q.where(or_(User.username.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like)))
        if search.isdigit():
            q = select(User).where(or_(User.id == int(search), User.username.ilike(like))).order_by(User.created_at.desc())
    res = await session.execute(q.limit(limit).offset(offset))
    return list(res.scalars())


async def count_users(session: AsyncSession, since: datetime | None = None) -> int:
    q = select(func.count(User.id))
    if since:
        q = q.where(User.created_at >= since)
    return (await session.execute(q)).scalar_one()


async def count_vip_users(session: AsyncSession) -> int:
    q = select(func.count(User.id)).where(User.is_vip.is_(True))
    return (await session.execute(q)).scalar_one()


async def list_vip_users(session: AsyncSession, limit: int = 200, offset: int = 0) -> list[tuple[User, Subscription]]:
    """Юзеры с активной подпиской, отсортированы по дате окончания (сначала у кого раньше кончается, lifetime — в конец)."""
    res = await session.execute(
        select(User, Subscription)
        .join(Subscription, Subscription.user_id == User.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE)
        .order_by(Subscription.expires_at.is_(None), Subscription.expires_at.asc())
        .limit(limit)
        .offset(offset)
    )
    return [(u, s) for u, s in res.all()]


# ── Платежи ───────────────────────────────────────────────────────────────────

async def create_payment(
    session: AsyncSession,
    *,
    user_id: int,
    gateway: str,
    external_id: str,
    product_type: str,
    plan_key: str,
    plan_name: str,
    amount_usd: float,
    pay_url: str | None = None,
    status: str = PaymentStatus.PENDING,
) -> Payment:
    payment = Payment(
        user_id=user_id,
        gateway=gateway,
        external_id=external_id,
        product_type=product_type,
        plan_key=plan_key,
        plan_name=plan_name,
        amount_usd=amount_usd,
        pay_url=pay_url,
        status=status,
    )
    session.add(payment)
    await session.commit()
    return payment


async def pending_payments(session: AsyncSession) -> list[Payment]:
    res = await session.execute(select(Payment).where(Payment.status == PaymentStatus.PENDING))
    return list(res.scalars())


async def set_payment_status(session: AsyncSession, payment: Payment, status: str) -> None:
    payment.status = status
    await session.commit()


async def list_payments(session: AsyncSession, limit: int = 100, offset: int = 0) -> list[Payment]:
    res = await session.execute(
        select(Payment).order_by(Payment.created_at.desc()).limit(limit).offset(offset)
    )
    return list(res.scalars())


# ── Покупки ───────────────────────────────────────────────────────────────────

async def add_purchase(
    session: AsyncSession,
    *,
    user_id: int,
    product_type: str,
    plan_name: str,
    amount_usd: float,
    plan_key: str = "",
    payment_id: int | None = None,
) -> Purchase:
    purchase = Purchase(
        user_id=user_id,
        payment_id=payment_id,
        product_type=product_type,
        plan_key=plan_key,
        plan_name=plan_name,
        amount_usd=amount_usd,
    )
    session.add(purchase)
    await session.commit()
    return purchase


async def list_purchases(session: AsyncSession, limit: int = 100, offset: int = 0) -> list[tuple[Purchase, User | None]]:
    res = await session.execute(
        select(Purchase, User)
        .join(User, Purchase.user_id == User.id, isouter=True)
        .order_by(Purchase.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [(p, u) for p, u in res.all()]


async def latest_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    """Последняя подписка юзера независимо от статуса (для карточки в админке)."""
    res = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id)
        .order_by(Subscription.id.desc())
    )
    return res.scalars().first()


async def user_purchases(session: AsyncSession, user_id: int, limit: int = 20) -> list[Purchase]:
    res = await session.execute(
        select(Purchase)
        .where(Purchase.user_id == user_id)
        .order_by(Purchase.created_at.desc())
        .limit(limit)
    )
    return list(res.scalars())


async def purchases_stats(session: AsyncSession, since: datetime | None = None) -> tuple[int, float]:
    """(количество, сумма USD) покупок, опционально с даты."""
    q = select(func.count(Purchase.id), func.coalesce(func.sum(Purchase.amount_usd), 0.0))
    if since:
        q = q.where(Purchase.created_at >= since)
    row = (await session.execute(q)).one()
    return int(row[0]), float(row[1])


# ── Подписки ──────────────────────────────────────────────────────────────────

async def active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    res = await session.execute(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status == SubscriptionStatus.ACTIVE)
        .order_by(Subscription.id.desc())
    )
    return res.scalars().first()


async def active_subscriptions(session: AsyncSession) -> list[Subscription]:
    res = await session.execute(
        select(Subscription).where(Subscription.status == SubscriptionStatus.ACTIVE)
    )
    return list(res.scalars())


async def expire_subscription(session: AsyncSession, sub: Subscription) -> None:
    sub.status = SubscriptionStatus.EXPIRED
    user = await session.get(User, sub.user_id)
    if user:
        user.is_vip = False
    await session.commit()


# ── PocketOption-заявки ───────────────────────────────────────────────────────

async def create_pocket_order(
    session: AsyncSession,
    *,
    user_id: int,
    tier_index: int,
    amount_usd: float,
    balance_usd: float,
    payment_id: int | None = None,
) -> PocketOrder:
    order = PocketOrder(
        user_id=user_id,
        payment_id=payment_id,
        tier_index=tier_index,
        amount_usd=amount_usd,
        balance_usd=balance_usd,
    )
    session.add(order)
    await session.commit()
    return order


async def list_pocket_orders(session: AsyncSession, status: str | None = None) -> list[tuple[PocketOrder, User | None]]:
    q = (
        select(PocketOrder, User)
        .join(User, PocketOrder.user_id == User.id, isouter=True)
        .order_by(PocketOrder.created_at.desc())
    )
    if status:
        q = q.where(PocketOrder.status == status)
    res = await session.execute(q.limit(200))
    return [(o, u) for o, u in res.all()]


async def fulfill_pocket_order(session: AsyncSession, order: PocketOrder) -> None:
    order.status = PocketOrderStatus.FULFILLED
    order.fulfilled_at = utcnow()
    await session.commit()
