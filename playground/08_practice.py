"""Практика: задачи по Playground.

Решай задачи, заменяя pass-блоки своим кодом.
Внизу — проверка: вызывает каждую функцию и пишет PASS/FAIL.
Запуск: python 08_practice.py
"""


# ══════════════════════════════════════════════════════════════════
# COMPREHENSIONS
# ══════════════════════════════════════════════════════════════════

def task_01():
    """Квадраты нечётных от 1 до 20.
    Ожидается: [1, 9, 25, 49, 81, 121, 169, 225, 289, 361]
    """
    pass


def task_02():
    """Переверни словарь: ключи <-> значения.
    Вход: {"a": 1, "b": 2, "c": 3}
    Ожидается: {1: "a", 2: "b", 3: "c"}
    """
    data = {"a": 1, "b": 2, "c": 3}
    pass


def task_03():
    """Положительные из матрицы (плоский список).
    Вход: [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    Ожидается: [1, 3, 5, 7, 9]
    """
    matrix = [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    pass


def task_04():
    """Слово -> длина.
    Вход: ["hello", "world", "python", "hi"]
    Ожидается: {"hello": 5, "world": 5, "python": 6, "hi": 2}
    """
    words = ["hello", "world", "python", "hi"]
    pass


def task_05():
    """Уникальные первые буквы.
    Вход: ["apple", "banana", "avocado", "blueberry", "cherry"]
    Ожидается: {"a", "b", "c"}
    """
    fruits = ["apple", "banana", "avocado", "blueberry", "cherry"]
    pass


# ══════════════════════════════════════════════════════════════════
# THREADING
# ══════════════════════════════════════════════════════════════════

def task_06():
    """Lock: 2 потока + counter. С lock итог = 2_000_000.
    Ожидается: 2000000
    """
    import threading
    counter = 0
    lock = threading.Lock()

    def increment(n):
        nonlocal counter
        for _ in range(n):
            pass  # ← with lock: counter += 1

    pass  # ← создай 2 потока, запусти, дождись
    return counter


def task_07():
    """ThreadPoolExecutor: 5 запросов по 0.3сек, пул из 3.
    Верни (seq_time, par_time) — параллельно должно быть быстрее.
    """
    import concurrent.futures
    import time

    def fake_request(name, delay):
        time.sleep(delay)
        return f"{name}: OK"

    requests = [("A", 0.3), ("B", 0.3), ("C", 0.3), ("D", 0.3), ("E", 0.3)]
    pass  # ← замерь seq и par, верни tuple


# ══════════════════════════════════════════════════════════════════
# MULTIPROCESSING
# ══════════════════════════════════════════════════════════════════

def task_08():
    """Pool: heavy(n) = сумма квадратов. 4 процесса.
    Верни (seq_time, par_time).
    """
    from multiprocessing import Pool
    import time

    def heavy(n):
        return sum(i * i for i in range(n))

    data = [5_000_000] * 4
    pass  # ← замерь seq и par


def task_09():
    """Queue: producer кладёт 0..9, consumer считает сумму.
    Ожидается: 45
    """
    from multiprocessing import Process, Queue
    import multiprocessing

    def producer(q):
        pass  # ← put числа 0..9 + None

    def consumer(q, result):
        pass  # ← get, считай сумму

    pass  # ← создай Queue, запусти процессы


# ══════════════════════════════════════════════════════════════════
# TRICKY QUESTIONS
# ══════════════════════════════════════════════════════════════════

def task_10():
    """Исправь mutable default.
    Ожидается: [[1], [2], [3]]
    """
    def append_to(num, target=[]):
        pass  # ← if target is None: target = []
        target.append(num)
        return target

    return [append_to(1), append_to(2), append_to(3)]


def task_11():
    """Исправь late binding.
    Ожидается: [0, 1, 2, 3, 4]
    """
    funcs = []
    for i in range(5):
        pass  # ← lambda i=i: i

    return [f() for f in funcs]


def task_12():
    """Декоратор retry: вызывает функцию до times попыток.
    Ожидается: 'успех!'
    """
    import functools
    import random

    def retry(times):
        pass  # ← decorator + wrapper

    @retry(times=10)
    def flaky():
        if random.random() < 0.7:
            raise ValueError("ошибка")
        return "успех!"

    return flaky()


# ══════════════════════════════════════════════════════════════════
# METACLASSES
# ══════════════════════════════════════════════════════════════════

def task_13():
    """Singleton: только один экземпляр.
    Ожидается: True
    """
    class SingletonMeta(type):
        pass  # ← _instances + __call__

    class Database(metaclass=SingletonMeta):
        def __init__(self, url):
            self.url = url

    db1 = Database("pg://localhost")
    db2 = Database("sqlite://:memory:")
    return db1 is db2


def task_14():
    """Авто-__repr__ через метакласс.
    Ожидается: User(name='Алиса', age=25)
    """
    class ReprMeta(type):
        pass  # ← __new__ + annotations -> __repr__

    class User(metaclass=ReprMeta):
        name: str
        age: int
        def __init__(self, name, age):
            self.name = name
            self.age = age

    return repr(User("Алиса", 25))


# ══════════════════════════════════════════════════════════════════
# ASYNC
# ══════════════════════════════════════════════════════════════════

def task_15():
    """Async-замыкание: считает сумму 0..n, кэширует.
    Ожидается: (55, 55)
    """
    import asyncio

    def make_counter(n):
        pass  # ← async def counter() + nonlocal _cache

    async def run():
        c = make_counter(10)
        if c is None:
            return None
        first = await c()
        second = await c()
        return (first, second)

    return asyncio.run(run())


def task_16():
    """Async-генератор fibonacci(n) + lazy filter.
    Ожидается: ([0,1,1,2,3,5,8,13,21,34], [0,2,8,34])
    """
    import asyncio

    async def fibonacci(n):
        pass  # ← async yield

    async def lazy_filter(iterable, predicate):
        pass  # ← async for + yield

    async def run():
        fibs = [x async for x in fibonacci(10)]
        stream = fibonacci(10)
        evens = [x async for x in lazy_filter(stream, lambda x: x % 2 == 0)]
        return (fibs, evens)

    return asyncio.run(run())


# ══════════════════════════════════════════════════════════════════
# SQLALCHEMY
# ══════════════════════════════════════════════════════════════════

def task_17():
    """SQLAlchemy: модель Book + create + get_by_rating.
    Ожидается: список книг с rating >= 4.0
    """
    from sqlalchemy import Column, Float, Integer, String, select, create_engine
    from sqlalchemy.orm import Session, DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class Book(Base):
        __tablename__ = "books"
        id = Column(Integer, primary_key=True)
        title = Column(String(100))
        author = Column(String(100))
        pages = Column(Integer)
        rating = Column(Float)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        pass  # ← создай 3-4 книги, get_by_rating(4.0)


# ══════════════════════════════════════════════════════════════════
# ПРОВЕРКА
# ══════════════════════════════════════════════════════════════════

def check(name, got, expected):
    ok = got == expected
    print(f"  [{'OK' if ok else 'FAIL'}] {name}")
    if not ok:
        print(f"      получено:   {got}")
        print(f"      ожидалось:  {expected}")
    return ok


if __name__ == "__main__":
    print("=" * 55)
    print("  Практика — проверка ответов")
    print("=" * 55)
    print()

    r = []

    r.append(check("01: квадраты нечётных",
        task_01(), [1, 9, 25, 49, 81, 121, 169, 225, 289, 361]))

    r.append(check("02: переворот словаря",
        task_02(), {1: "a", 2: "b", 3: "c"}))

    r.append(check("03: положительные из матрицы",
        task_03(), [1, 3, 5, 7, 9]))

    r.append(check("04: слово -> длина",
        task_04(), {"hello": 5, "world": 5, "python": 6, "hi": 2}))

    r.append(check("05: первые буквы",
        task_05(), {"a", "b", "c"}))

    r.append(check("06: lock counter",
        task_06(), 2_000_000))

    r07 = task_07()
    if r07 and r07[0] > 0 and r07[1] > 0:
        ok = r07[1] < r07[0]
        r.append(check("07: threading speedup", ok, True))
        print(f"       seq={r07[0]:.2f} par={r07[1]:.2f}")
    else:
        r.append(check("07: threading", r07, "tuple"))

    r08 = task_08()
    if r08 and r08[0] > 0 and r08[1] > 0:
        ok = r08[1] < r08[0]
        r.append(check("08: multiprocessing speedup", ok, True))
        print(f"       seq={r08[0]:.2f} par={r08[1]:.2f}")
    else:
        r.append(check("08: multiprocessing", r08, "tuple"))

    r.append(check("09: queue sum",
        task_09(), 45))

    r.append(check("10: mutable default",
        task_10(), [[1], [2], [3]]))

    r.append(check("11: late binding",
        task_11(), [0, 1, 2, 3, 4]))

    r12 = task_12()
    r.append(check("12: retry decorator",
        r12 == "успех!", True))

    r.append(check("13: singleton",
        task_13(), True))

    r.append(check("14: auto __repr__",
        task_14(), "User(name='Алиса', age=25)"))

    r.append(check("15: async closure",
        task_15(), (55, 55)))

    r16 = task_16()
    if r16:
        r.append(check("16a: fibonacci",
            r16[0], [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]))
        r.append(check("16b: even fibonacci",
            r16[1], [0, 2, 8, 34]))
    else:
        r.append(check("16: fibonacci", None, "tuple"))

    r17 = task_17()
    r.append(check("17: sqlalchemy",
        r17 is not None, True))

    print()
    print("=" * 55)
    passed = sum(r)
    total = len(r)
    if passed == total:
        print(f"  Все {total} задач пройдены!")
    else:
        print(f"  Пройдено {passed}/{total}")
    print("=" * 55)
