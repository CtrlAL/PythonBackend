"""Практика: задачи по Playground.

Все задачи: pass-блоки, подсказки, НЕТ готовых решений.
3 задачи на поиск бага (закомментированы).
Запуск: python 08_practice.py
"""


# ══════════════════════════════════════════════════════════════════
# COMPREHENSIONS
# ══════════════════════════════════════════════════════════════════

def task_01():
    """Квадраты нечётных от 1 до 20.
    
    Ожидается: [1, 9, 25, 49, 81, 121, 169, 225, 289, 361]
    Подсказка: [x**2 for x in range(1, 21) if x % 2 != 0]
    """
    d = {x: x**2 if x % 2 == 0 else x**3 for x in range(1, 21)}

    return [x**2 for x in range(1,21) ]


def task_02():
    """Переверни словарь: ключи <-> значения.
    Вход: data = {"a": 1, "b": 2, "c": 3}
    Ожидается: {1: "a", 2: "b", 3: "c"}
    Подсказка: {v: k for k, v in data.items()}
    """
    data = {"a": 1, "b": 2, "c": 3}
    pass


def task_03():
    """Положительные из матрицы (плоский список).
    Вход: matrix = [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    Ожидается: [1, 3, 5, 7, 9]
    Подсказка: [x for row in matrix for x in row if x > 0]
    """
    matrix = [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    pass


def task_04():
    """Слово -> длина.
    Вход: words = ["hello", "world", "python", "hi"]
    Ожидается: {"hello": 5, "world": 5, "python": 6, "hi": 2}
    Подсказка: {w: len(w) for w in words}
    """
    words = ["hello", "world", "python", "hi"]
    pass


def task_05():
    """Уникальные первые буквы.
    Вход: fruits = ["apple", "banana", "avocado", "blueberry", "cherry"]
    Ожидается: {"a", "b", "c"}
    Подсказка: {f[0] for f in fruits}
    """
    fruits = ["apple", "banana", "avocado", "blueberry", "cherry"]
    pass


# ══════════════════════════════════════════════════════════════════
# THREADING
# ══════════════════════════════════════════════════════════════════

def task_06():
    """Lock: 2 потока + counter. Без lock гонка, с lock = 2_000_000.
    Ожидается: 2000000
    Подсказка: import threading, nonlocal counter, lock = threading.Lock()
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
    Ожидается: par_time < seq_time (примерно 2-3x ускорение)
    Подсказка: import concurrent.futures, pool.map(func, iterable)
    """
    import concurrent.futures
    import time

    def fake_request(name, delay):
        time.sleep(delay)
        return f"{name}: OK"

    requests = [("A", 0.3), ("B", 0.3), ("C", 0.3), ("D", 0.3), ("E", 0.3)]
    pass  # ← замерь seq и par, верни (seq_time, par_time)


# ══════════════════════════════════════════════════════════════════
# MULTIPROCESSING
# ══════════════════════════════════════════════════════════════════

def _heavy(n):
    """Вспомогательная функция для task_08 (должна быть на уровне модуля)."""
    return sum(i * i for i in range(n))


def task_08():
    """Pool: heavy(n) = сумма квадратов. 4 процесса.
    Ожидается: par_time < seq_time
    Подсказка: from multiprocessing import Pool, p.map(func, data)
    """
    from multiprocessing import Pool
    import time

    data = [5_000_000] * 4
    pass  # ← замерь seq и par, верни (seq_time, par_time)


def _producer(q):
    """Вспомогательная функция для task_09."""
    for i in range(10):
        q.put(i)
    q.put(None)


def _consumer(q, result):
    """Вспомогательная функция для task_09."""
    total = 0
    while True:
        item = q.get()
        if item is None:
            break
        total += item
    result.append(total)


def task_09():
    """Queue: producer кладёт 0..9, consumer считает сумму.
    Ожидается: 45
    Подсказка: Queue(), Process(target=..., args=(...)), mgr.list()
    """
    from multiprocessing import Process, Queue
    import multiprocessing

    pass  # ← создай Queue, запусти _producer и _consumer


# ══════════════════════════════════════════════════════════════════
# TRICKY QUESTIONS
# ══════════════════════════════════════════════════════════════════

def task_10():
    """БАГ: mutable default argument.
    Сейчас append_to(1), append_to(2), append_to(3) возвращают
    [1, 2, 3] три раза вместо [[1], [2], [3]].
    Найди баг и исправь.
    Ожидается: [[1], [2], [3]]
    Подсказка: default argument вычисляется ОДИН раз при определении функции
    """
    def append_to(num, target=[]):
        target.append(num)
        return target

    return [append_to(1), append_to(2), append_to(3)]


def task_11():
    """БАГ: late binding closures.
    Сейчас все lambda возвращают 4 вместо [0, 1, 2, 3, 4].
    Найди баг и исправь.
    Ожидается: [0, 1, 2, 3, 4]
    Подсказка: замыкание захватывает ПЕРЕМЕННУЮ, а не значение
    """
    funcs = []
    for i in range(5):
        funcs.append(lambda: i)

    return [f() for f in funcs]


def task_12():
    """Декоратор retry: вызывает функцию до times попыток.
    Ожидается: "успех!"
    Подсказка: decorator(func) -> wrapper, @functools.wraps(func)
    Замени тело retry на свою реализацию.
    """
    import functools
    import random

    def retry(times):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(times):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        print(f"  попытка {attempt + 1}: {e}")
                raise RuntimeError(f"все {times} попыток провалены")
            return wrapper
        return decorator

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
    """Singleton: только один экземпляр класса.
    Ожидается: True
    Подсказка: type.__new__ + __call__ + _instances dict
    """
    class SingletonMeta(type):
        pass  # ← _instances = {} + __call__ который проверяет cls in _instances

    class Database(metaclass=SingletonMeta):
        def __init__(self, url):
            self.url = url

    db1 = Database("pg://localhost")
    db2 = Database("sqlite://:memory:")
    return db1 is db2


def task_14():
    """Авто-__repr__ через метакласс.
    Ожидается: User(name='Алиса', age=25)
    Подсказка: annotations = namespace.get("__annotations__", {})
    """
    class ReprMeta(type):
        pass  # ← __new__: читай annotations, генерируй __repr__

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
    Подсказка: async def counter() + nonlocal _cache
    """
    import asyncio

    def make_counter(n):
        pass  # ← async def counter() с nonlocal _cache

    async def run():
        c = make_counter(10)
        if c is None:
            return None
        first = await c()
        second = await c()
        return (first, second)

    return asyncio.run(run())


def task_16():
    """БАГ: async-генератор fibonacci не работает.
    Сейчас 'async for x in fibonacci(10)' падает с TypeError.
    Найди баг и исправь.
    Ожидается: ([0,1,1,2,3,5,8,13,21,34], [0,2,8,34])
    Подсказка: async def + yield = async generator
    """
    import asyncio

    async def fibonacci(n):
        pass  # ← async def fibonacci(n): ... yield a ...

    async def lazy_filter(iterable, predicate):
        pass  # ← async for item in iterable: if predicate(item): yield item

    async def run():
        try:
            fibs = [x async for x in fibonacci(10)]
        except TypeError:
            return None
        stream = fibonacci(10)
        evens = [x async for x in lazy_filter(stream, lambda x: x % 2 == 0)]
        return (fibs, evens)

    return asyncio.run(run())


# ══════════════════════════════════════════════════════════════════
# SQLALCHEMY
# ══════════════════════════════════════════════════════════════════

def task_17():
    """SQLAlchemy: модель Book + create + get_by_rating.
    Ожидается: количество книг с rating >= 4.0
    Подсказка: session.add(Book(...)), session.commit(), select(Book).where(...)
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

    pass  # ← создай Session(engine), добавь 3-4 книги, сделай select, верни список


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
        r.append(check("07: threading seq > par", r07[0] > r07[1], True))
        print(f"       seq={r07[0]:.2f} par={r07[1]:.2f}")
    else:
        r.append(check("07: threading", r07, "(seq, par)"))

    r08 = task_08()
    if r08 and r08[0] > 0 and r08[1] > 0:
        r.append(check("08: multiprocessing seq > par", r08[0] > r08[1], True))
        print(f"       seq={r08[0]:.2f} par={r08[1]:.2f}")
    else:
        r.append(check("08: multiprocessing", r08, "(seq, par)"))

    r.append(check("09: queue sum",
        task_09(), 45))

    r.append(check("10: mutable default [БАГ]",
        task_10(), [[1], [2], [3]]))

    r.append(check("11: late binding [БАГ]",
        task_11(), [0, 1, 2, 3, 4]))

    r12 = task_12()
    r.append(check("12: retry decorator", r12 == "успех!", True))

    r.append(check("13: singleton",
        task_13(), True))

    r.append(check("14: auto __repr__",
        task_14(), "User(name='Алиса', age=25)"))

    r.append(check("15: async closure",
        task_15(), (55, 55)))

    r16 = task_16()
    if r16:
        r.append(check("16a: fibonacci [БАГ]",
            r16[0], [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]))
        r.append(check("16b: even fibonacci [БАГ]",
            r16[1], [0, 2, 8, 34]))
    else:
        r.append(check("16: fibonacci [БАГ]", None, "tuple"))

    r17 = task_17()
    r.append(check("17: sqlalchemy (3 книги >= 4.0)",
        len(r17) if r17 else 0, 3))

    print()
    print("=" * 55)
    passed = sum(r)
    total = len(r)
    print(f"  Пройдено: {passed}/{total}")
    print(f"  Баги: задачи 10, 11, 16 — найди и исправь")
    print("=" * 55)
