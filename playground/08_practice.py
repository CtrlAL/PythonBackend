"""Практика: задачи по Playground.

Решай задачи, заполняя pass-блоки.
Внизу файла — проверка: вызывает каждую функцию и сравнивает ответ.
Запуск: python 08_practice.py
"""


# ══════════════════════════════════════════════════════════════════
# COMPREHENSIONS
# ══════════════════════════════════════════════════════════════════

def task_01():
    """Список квадратов нечётных чисел от 1 до 20."""
    pass  # ← [x**2 for x in range(...) if ...]


def task_02():
    """Переверни словарь: ключи ↔ значения.

    Вход: {"a": 1, "b": 2, "c": 3}
    Ожидается: {1: "a", 2: "b", 3: "c"}
    """
    data = {"a": 1, "b": 2, "c": 3}
    pass  # ← {v: k for k, v in ...}


def task_03():
    """Плоский список из матрицы, только положительные.

    Вход: [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    Ожидается: [1, 3, 5, 7, 9]
    """
    matrix = [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    pass  # ← вложенная comprehension + фильтр


def task_04():
    """Слово → длина.

    Вход: ["hello", "world", "python", "hi"]
    Ожидается: {"hello": 5, "world": 5, "python": 6, "hi": 2}
    """
    words = ["hello", "world", "python", "hi"]
    pass  # ← {w: len(w) for w in ...}


def task_05():
    """Уникальные первые буквы.

    Вход: ["apple", "banana", "avocado", "blueberry", "cherry"]
    Ожидается: {'a', 'b', 'c'}
    """
    fruits = ["apple", "banana", "avocado", "blueberry", "cherry"]
    pass  # ← {f[0] for f in ...}


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
    """ThreadPoolExecutor: 5 запросов, пул из 3.

    Ожидается: время_параллельно < время_последовательно (примерно 2-3x)
    Верни (seq_time, par_time).
    """
    import concurrent.futures
    import time

    def fake_request(name, delay):
        time.sleep(delay)
        return f"{name}: OK"

    requests = [("A", 0.3), ("B", 0.3), ("C", 0.3), ("D", 0.3), ("E", 0.3)]

    pass  # ← замерь последовательно
    pass  # ← замерь в ThreadPoolExecutor
    # return (seq_time, par_time)


# ══════════════════════════════════════════════════════════════════
# MULTIPROCESSING
# ══════════════════════════════════════════════════════════════════

def task_08():
    """Pool: heavy(n) = сумма квадратов. 4 процесса.

    Ожидается: все результаты одинаковы, ускорение > 2x.
    Верни (seq_time, par_time).
    """
    from multiprocessing import Pool
    import time

    def heavy(n):
        return sum(i * i for i in range(n))

    data = [5_000_000] * 4
    pass  # ← замерь seq и par
    # return (seq_time, par_time)


def task_09():
    """Queue: producer кладёт 0..9, consumer считает сумму.

    Ожидается: 45
    """
    from multiprocessing import Process, Queue

    def producer(q):
        pass  # ← put числа 0..9 + None

    def consumer(q, result):
        pass  # ← get, считай сумму, result.append(total)

    pass  # ← создай Queue, запусти процессы
    # return total


# ══════════════════════════════════════════════════════════════════
# TRICKY QUESTIONS
# ══════════════════════════════════════════════════════════════════

def task_10():
    """Исправь mutable default.

    Ожидается: append_to(1) → [1], append_to(2) → [2], append_to(3) → [3]
    """
    def append_to(num, target=[]):
        pass  # ← target = [] if target is None else target
        target.append(num)
        return target

    return [append_to(1), append_to(2), append_to(3)]


def task_11():
    """Исправь late binding.

    Ожидается: [0, 1, 2, 3, 4]
    """
    funcs = []
    for i in range(5):
        funcs.append(lambda i=i: i)  # ← lambda i=i: i

    return [f() for f in funcs]


def task_12():
    """Декоратор retry: вызывает функцию до times попыток.

    Ожидается: если flaky падает — печатает попытки, возвращает результат.
    """
    import functools
    import random

    def retry(times):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                pass  # ← for attempt in range(times): try/except
            return wrapper
        return decorator

    @retry(times=5)
    def flaky():
        if random.random() < 0.7:
            raise ValueError("ошибка")
        return "успех!"

    return flaky()


# ══════════════════════════════════════════════════════════════════
# METACLASSES
# ══════════════════════════════════════════════════════════════════

def task_13():
    """Singleton: только один экземпляр класса.

    Ожидается: db1 is db2 → True
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
        pass  # ← __new__ + annotations → __repr__

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

    Ожидается: первый вызов = 55, повторный = 55 (из кэша).
    """
    import asyncio

    def make_counter(n):
        pass  # ← async def + nonlocal _cache

    async def run():
        counter = make_counter(10)
        first = await counter()
        second = await counter()
        return (first, second)

    return asyncio.run(run())


def task_16():
    """Async-генератор fibonacci(n) + lazy filter.

    Ожидается: фибо 10 = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
               чётные = [0, 2, 8, 34]
    """
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

    Ожидается: create → get_by_rating(4.0) → список книг с rating >= 4.0
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
        pass  # ← создай 3-4 книги, добавь в сессию
        pass  # ← get_by_rating(4.0)
        # return books


# ══════════════════════════════════════════════════════════════════
# ПРОВЕРКА
# ══════════════════════════════════════════════════════════════════

def check(name, got, expected):
    ok = got == expected
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {name}")
    if not ok:
        print(f"      олучено:   {got}")
        print(f"      ожидалось: {expected}")
    return ok


if __name__ == "__main__":
    print("=" * 55)
    print("  Практика — проверка ответов")
    print("=" * 55)
    print()

    results = []

    # 01
    results.append(check("01: квадраты нечётных",
        task_01(), [x**2 for x in range(1, 21) if x % 2 != 0]))

    # 02
    results.append(check("02: переворот словаря",
        task_02(), {1: "a", 2: "b", 3: "c"}))

    # 03
    results.append(check("03: положительные из матрицы",
        task_03(), [1, 3, 5, 7, 9]))

    # 04
    results.append(check("04: слово → длина",
        task_04(), {"hello": 5, "world": 5, "python": 6, "hi": 2}))

    # 05
    results.append(check("05: первые буквы",
        task_05(), {'a', 'b', 'c'}))

    # 06
    results.append(check("06: lock counter",
        task_06(), 2_000_000))

    # 07
    r07 = task_07()
    if r07:
        ok = r07[1] < r07[0]
        results.append(check("07: threading speedup", ok, True))
        print(f"       seq={r07[0]:.2f}сек par={r07[1]:.2f}сек")
    else:
        results.append(check("07: threading", False, True))

    # 08
    r08 = task_08()
    if r08:
        ok = r08[1] < r08[0]
        results.append(check("08: multiprocessing speedup", ok, True))
        print(f"       seq={r08[0]:.2f}сек par={r08[1]:.2f}сек")
    else:
        results.append(check("08: multiprocessing", False, True))

    # 09
    results.append(check("09: queue sum",
        task_09(), 45))

    # 10
    results.append(check("10: mutable default fix",
        task_10(), [[1], [2], [3]]))

    # 11
    results.append(check("11: late binding fix",
        task_11(), [0, 1, 2, 3, 4]))

    # 12
    r12 = task_12()
    results.append(check("12: retry decorator", r12 in ("успех!", None), True))

    # 13
    results.append(check("13: singleton",
        task_13(), True))

    # 14
    results.append(check("14: auto __repr__",
        task_14(), "User(name='Алиса', age=25)"))

    # 15
    results.append(check("15: async closure",
        task_15(), (55, 55)))

    # 16
    r16 = task_16()
    if r16:
        results.append(check("16a: fibonacci",
            r16[0], [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]))
        results.append(check("16b: even fibonacci",
            r16[1], [0, 2, 8, 34]))
    else:
        results.append(check("16: fibonacci", False, True))

    # 17
    r17 = task_17()
    if r17 is not None:
        results.append(check("17: sqlalchemy", True, True))
    else:
        results.append(check("17: sqlalchemy", False, True))

    # Итог
    passed = sum(results)
    total = len(results)
    print()
    print("=" * 55)
    if passed == total:
        print(f"  Все {total} задач пройдены!")
    else:
        print(f"  Пройдено {passed}/{total}")
    print("=" * 55)
