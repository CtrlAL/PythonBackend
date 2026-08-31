"""Асинхронность + SQLAlchemy ORM: замыкания, CRUD, ленивые пайплайны.

SQLAlchemy — стандарт ORM для Python. Работает через "движок" (engine)
и "сессии" (session). Под капотом отправляет SQL, но ты работаешь
с объектами (User, Product) а не со строками.

Зависимости: pip install sqlalchemy[asyncio] aiosqlite
Запуск:      python 02_async.py
"""

import asyncio
import os
import time
from collections.abc import AsyncIterator
from datetime import datetime

from sqlalchemy import Column, Float, Integer, String, select, func, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship


# ══════════════════════════════════════════════════════════════════
# 1. ОПРЕДЕЛЕНИЕ МОДЕЛЕЙ (как C# entity classes / EF Core models)
# ══════════════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(__file__), "playground.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    """Базовый класс для всех моделей. Как DbContext в EF Core."""
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    score = Column(Float, default=0.0)
    created_at = Column(String(30), default=lambda: datetime.now().isoformat())

    # Связь: один пользователь → много заказов
    orders = relationship("Order", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"User(id={self.id}, name='{self.name}', score={self.score})"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    user_id = Column(Integer, nullable=False)

    user = relationship("User", back_populates="orders", lazy="selectin")

    def __repr__(self) -> str:
        return f"Order(id={self.id}, product='{self.product}', amount={self.amount})"


# ══════════════════════════════════════════════════════════════════
# 2. СОЗДАНИЕ ДВИЖКА И СЕССИИ
# ══════════════════════════════════════════════════════════════════

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,          # True — логирует каждый SQL-запрос
    pool_size=5,         # макс. соединений в пуле
    future=True,         # SQLAlchemy 2.0 стиль
)

# Фабрика сессий — как DbContextFactory в EF Core
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # объекты живут после commit
)


async def init_db() -> None:
    """Создаёт таблицы и заполняет данными."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        users = [
            User(
                name=f"user_{i}",
                email=f"user_{i}@example.com",
                score=round(i * 0.1, 2),
            )
            for i in range(1, 1001)
        ]
        session.add_all(users)
        await session.commit()
        print(f"[db] создано {len(users)} пользователей")


# ══════════════════════════════════════════════════════════════════
# 3. CRUD: Create, Read, Update, Delete
# ══════════════════════════════════════════════════════════════════

async def demo_crud() -> None:
    """Полный цикл CRUD через SQLAlchemy."""
    async with async_session() as session:

        # ── CREATE ─────────────────────────────────────────────
        new_user = User(name="Алиса", email="alice@example.com", score=95.5)
        session.add(new_user)
        await session.commit()
        print(f"  CREATE: {new_user}")

        # ── READ (get by id) ───────────────────────────────────
        # refresh — перечитывает из БД (обновляет id, created_at)
        await session.refresh(new_user)
        print(f"  READ:   id={new_user.id}")

        # ── UPDATE ─────────────────────────────────────────────
        new_user.score = 100.0
        new_user.name = "Алиса Великая"
        await session.commit()
        await session.refresh(new_user)
        print(f"  UPDATE: {new_user}")

        # ── DELETE ─────────────────────────────────────────────
        await session.delete(new_user)
        await session.commit()
        print(f"  DELETE: Алиса удалена")


# ══════════════════════════════════════════════════════════════════
# 4. ЗАПРОСЫ: select, where, order_by, limit
# ══════════════════════════════════════════════════════════════════

async def fetch_users(min_score: float = 0.0, limit: int = 10) -> list[User]:
    """Читает пользователей из БД через SQLAlchemy select."""
    async with async_session() as session:
        # select() — аналог LINQ query
        stmt = (
            select(User)
            .where(User.score >= min_score)
            .order_by(User.score.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        users = result.scalars().all()  # scalars() — извлекает объекты
        return list(users)


async def fetch_users_stream(
    min_score: float = 0.0,
) -> AsyncIterator[User]:
    """Ленивый поток: отдаёт пользователей по одному.

    yield_per — SQLAlchemy читает по N строк за раз из БД,
    не загружая всё в память.
    """
    async with async_session() as session:
        stmt = (
            select(User)
            .where(User.score >= min_score)
            .order_by(User.score.desc())
        )
        result = await session.stream(stmt)  # stream — ленивое чтение
        async for row in result:
            yield row.scalars().one()


# ══════════════════════════════════════════════════════════════════
# 5. АГРЕГАЦИИ: count, avg, sum (как SQL GROUP BY)
# ══════════════════════════════════════════════════════════════════

async def demo_aggregations() -> None:
    async with async_session() as session:
        # COUNT
        count_stmt = select(func.count(User.id))
        count = (await session.execute(count_stmt)).scalar()
        print(f"  COUNT:  {count} пользователей")

        # AVG
        avg_stmt = select(func.avg(User.score))
        avg = (await session.execute(avg_stmt)).scalar()
        print(f"  AVG:    {avg:.2f}")

        # SUM
        sum_stmt = select(func.sum(User.score))
        total = (await session.execute(sum_stmt)).scalar()
        print(f"  SUM:    {total:.2f}")

        # MIN / MAX
        min_max = await session.execute(
            select(func.min(User.score), func.max(User.score))
        )
        min_s, max_s = min_max.one()
        print(f"  MIN:    {min_s:.2f}")
        print(f"  MAX:    {max_s:.2f}")

        # RAW SQL (когда ORM не хватает)
        result = await session.execute(
            text("SELECT name, score FROM users WHERE score > 90 ORDER BY score DESC LIMIT 5")
        )
        rows = result.all()
        print(f"\n  RAW SQL (score > 90):")
        for name, score in rows:
            print(f"    {name}: {score}")


# ══════════════════════════════════════════════════════════════════
# 6. ПАРАЛЛЕЛЬНЫЕ ЗАПРОСЫ: asyncio.gather
# ══════════════════════════════════════════════════════════════════

async def demo_parallel() -> None:
    """3 запроса к БД параллельно через asyncio.gather."""
    t0 = time.perf_counter()

    results = await asyncio.gather(
        fetch_users(min_score=5.0, limit=100),
        fetch_users(min_score=8.0, limit=100),
        fetch_users(min_score=9.5, limit=100),
    )

    elapsed = time.perf_counter() - t0
    labels = ["score >= 5.0", "score >= 8.0", "score >= 9.5"]
    for label, users in zip(labels, results):
        print(f"  {label}: {len(users)} записей")
    print(f"  3 параллельных запроса: {elapsed:.3f} сек")


# ══════════════════════════════════════════════════════════════════
# 7. АСИНХРОННЫЕ ЗАМЫКАНИЯ
# ══════════════════════════════════════════════════════════════════

def make_filter(min_score: float) -> callable:
    """Замыкание: захватывает min_score, кэширует результат."""
    _cache: list[User] = []

    async def filter_users() -> list[User]:
        nonlocal _cache
        if not _cache:
            _cache = await fetch_users(min_score=min_score, limit=1000)
        return _cache

    return filter_users


def demo_closures() -> None:
    high_scorers = make_filter(min_score=8.0)
    mid_scorers = make_filter(min_score=4.0)

    async def run() -> None:
        result_high = await high_scorers()
        result_mid = await mid_scorers()
        print(f"  score >= 8.0: {len(result_high)} пользователей")
        print(f"  score >= 4.0: {len(result_mid)} пользователей")

        # Второй вызов — из кэша (мгновенно)
        t0 = time.perf_counter()
        await high_scorers()
        elapsed = time.perf_counter() - t0
        print(f"  повторный вызов (кэш): {elapsed:.6f} сек")

    asyncio.run(run())


# ══════════════════════════════════════════════════════════════════
# 8. ЛЕНИВЫЕ ВЫЧИСЛЕНИЯ: map → filter → reduce
# ══════════════════════════════════════════════════════════════════

async def lazy_map(iterable: AsyncIterator, fn: callable) -> AsyncIterator:
    """Ленивое преобразование: fn применяется только при итерации."""
    async for item in iterable:
        yield fn(item)


async def lazy_filter(iterable: AsyncIterator, predicate: callable) -> AsyncIterator:
    """Ленивая фильтрация."""
    async for item in iterable:
        if predicate(item):
            yield item


async def lazy_reduce(iterable: AsyncIterator, fn: callable, initial):
    """Ленивое свёртывание (consume)."""
    acc = initial
    async for item in iterable:
        acc = fn(acc, item)
    return acc


def demo_lazy() -> None:
    async def run() -> None:
        # Поток из БД → ленивое преобразование → фильтрация → consume
        stream = fetch_users_stream(min_score=0.0)

        # Шаг 1: лениво домножаем score на 2
        doubled = lazy_map(stream, lambda u: User(
            id=u.id, name=u.name, email=u.email, score=u.score * 2
        ))

        # Шаг 2: лениво фильтруем score >= 16
        filtered = lazy_filter(doubled, lambda u: u.score >= 16.0)

        # Шаг 3: consume — только теперь данные реально читаются из БД
        results = [user async for user in filtered]
        print(f"  ленивый пайплайн: {len(results)} пользователей (score*2 >= 16)")
        if results:
            print(f"  пример: {results[0].name} — score: {results[0].score}")
            print(f"  пример: {results[-1].name} — score: {results[-1].score}")

        # Reduce: сумма всех score*2
        stream2 = fetch_users_stream(min_score=0.0)
        doubled2 = lazy_map(stream2, lambda u: u.score * 2)
        total = await lazy_reduce(doubled2, lambda acc, s: acc + s, 0.0)
        print(f"\n  сумма (score*2): {total:.2f}")

    asyncio.run(run())


# ══════════════════════════════════════════════════════════════════
# 9. СВЯЗИ: один-ко-многим (User → Orders)
# ══════════════════════════════════════════════════════════════════

async def demo_relationships() -> None:
    async with async_session() as session:
        # Создаём пользователя с заказами
        user = User(name="Борис", email="boris@example.com", score=75.0)
        user.orders = [
            Order(product="Ноутбук", amount=999.99),
            Order(product="Мышь", amount=29.99),
            Order(product="Клавиатура", amount=59.99),
        ]
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"  создан: {user.name} (id={user.id})")

        # Читаем обратно — SQLAlchemy подгружает orders автоматически
        stmt = select(User).where(User.name == "Борис")
        result = await session.execute(stmt)
        boris = result.scalars().one()

        print(f"  заказы {boris.name}:")
        for order in boris.orders:
            print(f"    - {order.product}: {order.amount} руб.")

        # joins: SELECT users.name, orders.product FROM users JOIN orders ...
        stmt_joined = (
            select(User.name, Order.product, Order.amount)
            .join(Order, User.id == Order.user_id)
            .where(Order.amount > 50)
        )
        result_joined = await session.execute(stmt_joined)
        print(f"\n  JOIN (amount > 50):")
        for name, product, amount in result_joined:
            print(f"    {name} → {product}: {amount} руб.")


# ══════════════════════════════════════════════════════════════════
# 10. ТРАНЗАКЦИИ: commit / rollback
# ══════════════════════════════════════════════════════════════════

async def demo_transactions() -> None:
    async with async_session() as session:
        # Успешная транзакция
        async with session.begin():
            session.add(User(name="Транзакция_ОК", email="ok@test.com", score=1.0))
        print("  транзакция 1: COMMIT (OK)")

        # Откат транзакции
        try:
            async with session.begin():
                session.add(User(name="Транзакция_FAIL", email="ok@test.com", score=2.0))
                # email дублируется → IntegrityError → автоматический ROLLBACK
        except Exception as e:
            print(f"  транзакция 2: ROLLBACK ({type(e).__name__})")

        # Проверяем: вторая запись НЕ попала в БД
        stmt = select(User).where(User.name.like("Транзакция_%"))
        result = await session.execute(stmt)
        users = result.scalars().all()
        print(f"  в БД только: {[u.name for u in users]}")


# ══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════

async def main() -> None:
    await init_db()

    print("\n" + "=" * 55)
    print("1. CRUD: Create → Read → Update → Delete")
    print("=" * 55)
    await demo_crud()

    print("\n" + "=" * 55)
    print("2. Агрегации: COUNT, AVG, SUM, RAW SQL")
    print("=" * 55)
    await demo_aggregations()

    print("\n" + "=" * 55)
    print("3. Параллельные запросы (asyncio.gather)")
    print("=" * 55)
    await demo_parallel()

    print("\n" + "=" * 55)
    print("4. Async-замыкания с кэшированием")
    print("=" * 55)
    demo_closures()

    print("\n" + "=" * 55)
    print("5. Ленивый пайплайн: map → filter → reduce")
    print("=" * 55)
    await demo_lazy()

    print("\n" + "=" * 55)
    print("6. Связи: один-ко-многим (User → Orders)")
    print("=" * 55)
    await demo_relationships()

    print("\n" + "=" * 55)
    print("7. Транзакции: commit / rollback")
    print("=" * 55)
    await demo_transactions()

    # Уборка
    await engine.dispose()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"\n[db] {DB_PATH} удалён")


if __name__ == "__main__":
    asyncio.run(main())
