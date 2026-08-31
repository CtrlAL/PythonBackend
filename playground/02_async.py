"""Асинхронность: замыкания, SQLite, ленивые вычисления.

Ключевые концепции:
  - async/await и event loop
  - async-замыкания (capture + lazy evaluation)
  - aiosqlite: асинхронный доступ к SQLite
  - async-генераторы для ленивой обработки данных

Зависимость: pip install aiosqlite
Запуск:       python 02_async.py
"""

import asyncio
import os
import sqlite3
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

try:
    import aiosqlite
except ImportError:
    aiosqlite = None  # type: ignore[assignment]


DB_PATH = os.path.join(os.path.dirname(__file__), "playground.db")


# ── Модель данных ─────────────────────────────────────────────────

@dataclass
class User:
    id: int
    name: str
    email: str
    score: float


# ── Подготовка БД (синхронно, один раз) ───────────────────────────

def init_db() -> None:
    """Создаёт SQLite и заполняет 1000 пользователей."""
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        DROP TABLE IF EXISTS users;
        CREATE TABLE users (
            id    INTEGER PRIMARY KEY,
            name  TEXT NOT NULL,
            email TEXT NOT NULL,
            score REAL NOT NULL
        );
    """)

    rows = [
        (i, f"user_{i}", f"user_{i}@example.com", round(i * 0.1, 2))
        for i in range(1, 1001)
    ]
    conn.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    print(f"[db] создано {len(rows)} записей в {DB_PATH}")


# ── 1. Async-замыкания ────────────────────────────────────────────

def make_filter(min_score: float) -> callable:
    """Замыкание: захватывает min_score и фильтрует пользователей.

    Возвращает корутину, которую можно вызвать await'ом.
    """
    # Ленивая переменная — вычислится только при первом вызове
    _cache: list[User] = []

    async def filter_users(users: list[User]) -> list[User]:
        nonlocal _cache
        if not _cache:
            # Имитируем задержку (как будто обработка занимает время)
            await asyncio.sleep(0.01)
            _cache = [u for u in users if u.score >= min_score]
        return _cache

    return filter_users  # type: ignore[return-value]


def demo_closures() -> None:
    users = [User(i, f"u{i}", f"u{i}@mail.com", round(i * 0.1, 2))
             for i in range(1, 101)]

    high_scorers = make_filter(min_score=8.0)
    mid_scorers = make_filter(min_score=4.0)

    async def run() -> None:
        result_high = await high_scorers(users)
        result_mid = await mid_scorers(users)
        print(f"  score >= 8.0: {len(result_high)} пользователей")
        print(f"  score >= 4.0: {len(result_mid)} пользователей")

        # Второй вызов — из кэша (мгновенно)
        t0 = time.perf_counter()
        await high_scorers(users)
        elapsed = time.perf_counter() - t0
        print(f"  повторный вызов (кэш): {elapsed:.6f} сек")

    asyncio.run(run())


# ── 2. Асинхронное чтение SQLite ──────────────────────────────────

async def fetch_users(min_score: float = 0.0) -> list[User]:
    """Читает пользователей из SQLite через aiosqlite."""
    if aiosqlite is None:
        print("  [skip] aiosqlite не установлен, пропускаю")
        return []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE score >= ? ORDER BY score DESC",
            (min_score,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [User(**dict(row)) for row in rows]


async def fetch_users_stream(min_score: float = 0.0) -> AsyncIterator[User]:
    """Ленивый поток: отдаёт пользователей по одному."""
    if aiosqlite is None:
        return

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM users WHERE score >= ? ORDER BY score DESC",
            (min_score,),
        ) as cursor:
            async for row in cursor:
                yield User(**dict(row))


def demo_async_sqlite() -> None:
    async def run() -> None:
        t0 = time.perf_counter()

        # Параллельные запросы
        results = await asyncio.gather(
            fetch_users(min_score=5.0),
            fetch_users(min_score=8.0),
            fetch_users(min_score=9.5),
        )

        elapsed = time.perf_counter() - t0
        for i, (label, threshold) in enumerate(
            [("score >= 5.0", 5.0), ("score >= 8.0", 8.0), ("score >= 9.5", 9.5)]
        ):
            print(f"  {label}: {len(results[i])} записей")
        print(f"  3 параллельных запроса: {elapsed:.3f} сек")

        # Ленивый поток
        print("\n  --- ленивый поток (первые 5 из score >= 9.0) ---")
        count = 0
        async for user in fetch_users_stream(min_score=9.0):
            if count < 5:
                print(f"    {user.name} — score: {user.score}")
            count += 1
        print(f"  всего в потоке: {count}")

    asyncio.run(run())


# ── 3. Ленивые вычисления над данными ─────────────────────────────

async def lazy_map(
    iterable: AsyncIterator, fn: callable
) -> AsyncIterator:
    """Ленивое преобразование: fn применяется только при итерации."""
    async for item in iterable:
        yield fn(item)


async def lazy_filter(
    iterable: AsyncIterator, predicate: callable
) -> AsyncIterator:
    """Ленивая фильтрация."""
    async for item in iterable:
        if predicate(item):
            yield item


async def lazy_reduce(
    iterable: AsyncIterator, fn: callable, initial
):
    """Ленивое свёртывание (consume)."""
    acc = initial
    async for item in iterable:
        acc = await fn(acc, item) if asyncio.iscoroutinefunction(fn) else fn(acc, item)
    return acc


def demo_lazy() -> None:
    async def run() -> None:
        # Поток из БД → ленивое преобразование → ленивая фильтрация → consume
        stream = fetch_users_stream(min_score=0.0)

        # Шаг 1: лениво домножаем score на 2
        doubled = lazy_map(stream, lambda u: User(u.id, u.name, u.email, u.score * 2))

        # Шаг 2: лениво фильтруем score >= 16
        filtered = lazy_filter(doubled, lambda u: u.score >= 16.0)

        # Шаг 3: consume — только теперь данные реально читаются
        results = [user async for user in filtered]
        print(f"  ленивый пайплайн: {len(results)} пользователей (score*2 >= 16)")
        print(f"  пример: {results[0].name} — score: {results[0].score}")
        print(f"  пример: {results[-1].name} — score: {results[-1].score}")

        # Reduce: сумма всех score*2
        stream2 = fetch_users_stream(min_score=0.0)
        doubled2 = lazy_map(stream2, lambda u: u.score * 2)
        total = await lazy_reduce(doubled2, lambda acc, s: acc + s, 0.0)
        print(f"\n  сумма (score*2): {total:.2f}")

    asyncio.run(run())


# ── Запуск ────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()

    print("\n" + "=" * 50)
    print("1. Async-замыкания с кэшированием")
    print("=" * 50)
    demo_closures()

    print("\n" + "=" * 50)
    print("2. Параллельные запросы к SQLite + ленивый поток")
    print("=" * 50)
    demo_async_sqlite()

    print("\n" + "=" * 50)
    print("3. Ленивый пайплайн: map → filter → reduce")
    print("=" * 50)
    demo_lazy()

    # Уборка
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"\n[db] {DB_PATH} удалён")
