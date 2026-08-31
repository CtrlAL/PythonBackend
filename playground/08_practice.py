"""Практика: задачи по всем темам из Playground.

Перед каждой задачей — описание, пример вывода и подсказка.
Реши сам, используй 01–07 модули как ориентир.
Запуск: python 08_practice.py (или решай в Jupyter/IDE)

Когда будешь готов — проверь себя по решению в конце файла.
"""


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 1: LIST/DICT/SET COMPREHENSIONS
# ══════════════════════════════════════════════════════════════════

def task_01():
    """Задача 1: Создай список квадратов нечётных чисел от 1 до 20.

    Ожидаемый вывод: [1, 9, 25, 49, 81, 121, 169, 225, 289, 361]
    Подсказка: [x**2 for x in range(...) if ...]
    """
    pass  # ← напиши свой код здесь


def task_02():
    """Задача 2: Переверни словарь (ключи ↔ значения).

    Вход: {"a": 1, "b": 2, "c": 3}
    Выход: {1: "a", 2: "b", 3: "c"}
    Подсказка: {v: k for k, v in ...}
    """
    data = {"a": 1, "b": 2, "c": 3}
    pass  # ← напиши свой код здесь


def task_03():
    """Задача 3: Плоский список из матрицы 3x3, но только положительные.

    Вход: [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    Выход: [1, 3, 5, 7, 9]
    Подсказка: вложенная comprehension + фильтр
    """
    matrix = [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
    pass  # ← напиши свой код здесь


def task_04():
    """Задача 4: Создай dict, где ключ — слово, значение — его длина.

    Вход: ["hello", "world", "python", "hi"]
    Выход: {"hello": 5, "world": 5, "python": 6, "hi": 2}
    """
    words = ["hello", "world", "python", "hi"]
    pass  # ← напиши свой код здесь


def task_05():
    """Задача 5: Set comprehension — уникальные первые буквы слов.

    Вход: ["apple", "banana", "avocado", "blueberry", "cherry"]
    Выход: {'a', 'b', 'c'}  (порядок не важен)
    """
    fruits = ["apple", "banana", "avocado", "blueberry", "cherry"]
    pass  # ← напиши свой код здесь


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 2: THREADING
# ══════════════════════════════════════════════════════════════════

def task_06():
    """Задача 6: Потоки + Lock.

    Создай 2 потока, каждый прибавляет к counter по 1_000_000 раз.
    Без lock результат будет < 2_000_000. С lock — ровно 2_000_000.
    Выведи итог.

    Ожидаемый вывод: итог: 2000000 (ожидаем 2,000,000)
    """
    import threading
    counter = 0
    lock = threading.Lock()

    def increment(n):
        nonlocal counter
        for _ in range(n):
            pass  # ← напиши свой код здесь

    # Создай 2 потока, запусти, дождись
    pass  # ← напиши свой код здесь


def task_07():
    """Задача 7: ThreadPoolExecutor — параллельные запросы.

    Функция fake_request(name, delay) спит delay секунд и возвращает строку.
    Запусти 5 запросов с разными задержками в пуле из 3 потоков.
    Замерь время: последовательно vs параллельно.

    Ожидаемый вывод (пример):
      последовательно: 2.50 сек
      параллельно:     1.00 сек
      ускорение:        2.5x
    """
    import concurrent.futures
    import time

    def fake_request(name, delay):
        time.sleep(delay)
        return f"{name}: данные получены"

    requests = [("API-1", 0.5), ("API-2", 0.5), ("API-3", 0.5), ("API-4", 0.5), ("API-5", 0.5)]

    # Замерь последовательно
    pass  # ← напиши свой код здесь

    # Замерь в ThreadPoolExecutor
    pass  # ← напиши свой код здесь


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 3: MULTIPROCESSING
# ══════════════════════════════════════════════════════════════════

def task_08():
    """Задача 8: Pool — CPU-bound вычисления.

    Функция heavy(n) считает сумму квадратов от 0 до n.
    Запусти [10_000_000] × 4 через Pool(4) и замерь время.

    Ожидаемый вывод (пример):
      последовательно: 4.00 сек
      4 процесса:      1.10 сек
      ускорение:        3.6x
    """
    from multiprocessing import Pool
    import time

    def heavy(n):
        return sum(i * i for i in range(n))

    data = [10_000_000] * 4
    pass  # ← напиши свой код здесь


def task_09():
    """Задача 9: Queue — producer-consumer.

    Producer кладёт числа 0..9 в очередь.
    Consumer достаёт и считает сумму.
    Используй стоп-сигнал None.

    Ожидаемый вывод: сумма: 45
    """
    from multiprocessing import Process, Queue

    def producer(q):
        pass  # ← клади числа 0..9 + None

    def consumer(q, result):
        pass  # ← доставай числа и считай сумму

    pass  # ← напиши свой код здесь


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 4: TRICKY QUESTIONS
# ══════════════════════════════════════════════════════════════════

def task_10():
    """Задача 10: Исправь mutable default.

    Сейчас append_to возвращает [1, 2, 3] вместо [3].
    Исправь, чтобы каждый вызов возвращал новый список.
    """
    def append_to(num, target=[]):
        target.append(num)
        return target

    print(append_to(1))  # должен быть [1]
    print(append_to(2))  # должен быть [2]
    print(append_to(3))  # должен быть [3]


def task_11():
    """Задача 11: Исправь late binding.

    Сейчас все lambda возвращают 4.
    Исправь, чтобы возвращали 0, 1, 2, 3, 4.
    """
    funcs = []
    for i in range(5):
        funcs.append(lambda: i)

    print([f() for f in funcs])  # должен быть [0, 1, 2, 3, 4]


def task_12():
    """Задача 12: Напиши свой декоратор retry.

    Декоратор должен:
    - принимать аргумент times (количество попыток)
    - вызывать функцию до times попыток
    - при ошибке печатать номер попытки
    - если все попытки провалились — raise RuntimeError

    Ожидаемый вывод (пример, если 3-я попытка успешна):
      попытка 1: ValueError
      попытка 2: ValueError
      результат: успех!
    """
    import functools
    import random

    def retry(times):
        pass  # ← напиши декоратор здесь

    @retry(times=5)
    def flaky():
        if random.random() < 0.7:
            raise ValueError("случайная ошибка")
        return "успех!"

    print(f"результат: {flaky()}")


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 5: METACLASSES
# ══════════════════════════════════════════════════════════════════

def task_13():
    """Задача 13: Singleton через метакласс.

    Создай метакласс SingletonMeta, который гарантирует
    только один экземпляр класса.

    Ожидаемый вывод: db1 is db2: True
    """
    class SingletonMeta(type):
        pass  # ← напиши метакласс здесь

    class Database(metaclass=SingletonMeta):
        def __init__(self, url):
            self.url = url

    db1 = Database("postgresql://localhost")
    db2 = Database("sqlite://:memory:")
    print(f"db1 is db2: {db1 is db2}")  # True


def task_14():
    """Задача 14: Автоматический __repr__ через метакласс.

    Создай метакласс, который автоматически добавляет __repr__
    на основе __annotations__ класса.

    Ожидаемый вывод: User(name='Алиса', age=25)
    """
    class ReprMeta(type):
        pass  # ← напиши метакласс здесь

    class User(metaclass=ReprMeta):
        name: str
        age: int

        def __init__(self, name, age):
            self.name = name
            self.age = age

    print(User("Алиса", 25))


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 6: ASYNC
# ══════════════════════════════════════════════════════════════════

def task_15():
    """Задача 15: Async-замыкание с кэшированием.

    Замыкание make_counter() должно возвращать корутину,
    которая считает от 0 до n и кэширует результат.
    Повторный вызов — из кэша.

    Ожидаемый вывод:
      первый:  55
      кэш:     0.00000x сек
    """
    import asyncio

    def make_counter(n):
        pass  # ← напиши замыкание здесь

    async def run():
        counter = make_counter(10)
        result = await counter()
        print(f"первый:  {result}")

        import time
        t0 = time.perf_counter()
        result2 = await counter()
        elapsed = time.perf_counter() - t0
        print(f"кэш:     {elapsed:.6f} сек")

    asyncio.run(run())


def task_16():
    """Задача 16: Async-генератор + lazy map/filter.

    1. Напиши async-генератор fibonacci(n) — первые n чисел Фибоначчи.
    2. Напиши lazy_map — применяет функцию к каждому элементу.
    3. Напиши lazy_filter — фильтрует по предикату.

    Ожидаемый вывод:
      фибо: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
      чётные фибо: [0, 2, 8, 34]
    """
    async def fibonacci(n):
        pass  # ← async-генератор здесь

    async def lazy_map(iterable, fn):
        pass  # ← lazy map здесь

    async def lazy_filter(iterable, predicate):
        pass  # ← lazy filter здесь

    async def run():
        fibs = [x async for x in fibonacci(10)]
        print(f"фибо: {fibs}")

        stream = fibonacci(10)
        evens = lazy_filter(stream, lambda x: x % 2 == 0)
        result = [x async for x in evens]
        print(f"чётные фибо: {result}")

    asyncio.run(run())


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 7: SQLALCHEMY
# ══════════════════════════════════════════════════════════════════

def task_17():
    """Задача 17: SQLAlchemy — модель + CRUD.

    1. Создай модель Book с полями: id, title, author, pages, rating.
    2. Напиши функцию create_book(session, title, author, pages, rating).
    3. Напиши функцию get_books_by_rating(session, min_rating).
    4. Напиши функцию update_rating(session, book_id, new_rating).

    Зависимости: pip install sqlalchemy[asyncio] aiosqlite
    """
    from sqlalchemy import Column, Float, Integer, String, select, update
    from sqlalchemy.ext.asyncio import AsyncSession

    class Book:
        pass  # ← опиши модель здесь

    async def create_book(session, title, author, pages, rating):
        pass  # ← CRUD здесь

    async def get_books_by_rating(session, min_rating):
        pass  # ← фильтрация здесь

    async def update_rating(session, book_id, new_rating):
        pass  # ← update здесь


def task_18():
    """Задача 18: SQLAlchemy — JOIN + агрегация.

    Дано: User → Order → OrderItem → Product (см. 07_sqlalchemy_crud.py).

    Напиши запрос:
    1. Вывести имя пользователя и сумму его покупок.
    2. Только пользователи с суммой > 1000.
    3. Отсортировать по убыванию суммы.

    Ожидаемый формат: [("Алиса", 1234.56), ("Борис", 1100.00), ...]
    """
    pass  # ← напиши запрос здесь


def task_19():
    """Задача 19: SQLAlchemy — Window functions.

    Дано: User → Order → OrderItem.

    Напиши запрос с RANK(): ранжируй пользователей по сумме покупок.
    Формат: (имя, сумма, ранг)

    Ожидаемый формат: [("Алиса", 5000, 1), ("Борис", 3000, 2), ...]
    """
    pass  # ← напиши запрос здесь


# ══════════════════════════════════════════════════════════════════
# УРОВЕНЬ 8: БОНУС (сложные)
# ══════════════════════════════════════════════════════════════════

def task_20():
    """Задача 20: Бонус — комбинация async + threading.

    Ситуация: у тебя 3 API, каждое отвечает за 0.3 сек.
    Но одно из них — блокирующее (sleep), его надо запускать в потоке.

    Задачи:
    1. Напиши async-функцию fetch_async(name) — спит 0.3 сек.
    2. Напиши async-функцию fetch_blocking(name) — использует asyncio.to_thread(time.sleep, 0.3).
    3. Запусти все 3 параллельно через asyncio.gather.

    Ожидаемый вывод: ~0.3 сек (не 0.9!)
    """
    import asyncio
    import time

    async def fetch_async(name):
        pass  # ← async-запрос

    async def fetch_blocking(name):
        pass  # ← блокирующий в потоке

    async def run():
        t0 = time.perf_counter()
        results = await asyncio.gather(
            fetch_async("API-1"),
            fetch_blocking("API-2"),
            fetch_async("API-3"),
        )
        elapsed = time.perf_counter() - t0
        print(f"результаты: {results}")
        print(f"время: {elapsed:.2f} сек (ожидаем ~0.3)")

    asyncio.run(run())


# ══════════════════════════════════════════════════════════════════
# ЗАПУСК ПРОВЕРКИ
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Python Playground — Практика")
    print("=" * 60)
    print()
    print("Этот файл содержит 20 задач для самостоятельного решения.")
    print()
    print("Как пользоваться:")
    print("  1. Открой этот файл в IDE")
    print("  2. Закомментируй solve=True ниже")
    print("  3. Решай задачи по порядку")
    print("  4. Запускай отдельные функции task_NN()")
    print("  5. Сверяйся с ориентиром из 01–07 модулей")
    print()
    print("Для проверки раскомментируй solve=True")
    print()

    solve = False  # ← раскомментируй чтобы проверить решения

    if solve:
        print("РЕШЕНИЯ:")
        print("-" * 60)

        # 01
        result = [x**2 for x in range(1, 21) if x % 2 != 0]
        print(f"01: {result}")

        # 02
        data = {"a": 1, "b": 2, "c": 3}
        result = {v: k for k, v in data.items()}
        print(f"02: {result}")

        # 03
        matrix = [[1, -2, 3], [-4, 5, -6], [7, -8, 9]]
        result = [x for row in matrix for x in row if x > 0]
        print(f"03: {result}")

        # 04
        words = ["hello", "world", "python", "hi"]
        result = {w: len(w) for w in words}
        print(f"04: {result}")

        # 05
        fruits = ["apple", "banana", "avocado", "blueberry", "cherry"]
        result = {f[0] for f in fruits}
        print(f"05: {result}")

        # 06
        import threading
        counter = 0
        lock = threading.Lock()

        def increment(n):
            global counter
            for _ in range(n):
                with lock:
                    counter += 1

        t1 = threading.Thread(target=increment, args=(1_000_000,))
        t2 = threading.Thread(target=increment, args=(1_000_000,))
        t1.start(); t2.start()
        t1.join(); t2.join()
        print(f"06: итог: {counter} (ожидаем 2,000,000)")

        # 07
        import concurrent.futures
        import time

        def fake_request(name, delay):
            time.sleep(delay)
            return f"{name}: OK"

        requests = [("A", 0.5), ("B", 0.5), ("C", 0.5), ("D", 0.5), ("E", 0.5)]

        t0 = time.perf_counter()
        seq = [fake_request(n, d) for n, d in requests]
        seq_time = time.perf_counter() - t0

        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            par = list(pool.map(lambda r: fake_request(*r), requests))
        par_time = time.perf_counter() - t0
        print(f"07: последовательно: {seq_time:.2f} сек, параллельно: {par_time:.2f} сек, ускорение: {seq_time/par_time:.1f}x")

        # 08
        from multiprocessing import Pool
        import time

        def heavy(n):
            return sum(i * i for i in range(n))

        data = [10_000_000] * 4
        t0 = time.perf_counter()
        seq = [heavy(x) for x in data]
        seq_t = time.perf_counter() - t0
        t0 = time.perf_counter()
        with Pool(4) as p:
            par = p.map(heavy, data)
        par_t = time.perf_counter() - t0
        print(f"08: seq={seq_t:.2f}сек, par={par_t:.2f}сек, speedup={seq_t/par_t:.1f}x")

        # 09
        from multiprocessing import Process, Queue

        def prod(q):
            for i in range(10):
                q.put(i)
            q.put(None)

        def cons(q, result):
            total = 0
            while True:
                item = q.get()
                if item is None: break
                total += item
            result.append(total)

        q = Queue()
        mgr = __import__("multiprocessing").Manager()
        res = mgr.list()
        p1 = Process(target=prod, args=(q,))
        p2 = Process(target=cons, args=(q, res))
        p1.start(); p2.start()
        p1.join(); p2.join()
        print(f"09: сумма: {res[0]}")

        # 10
        def append_to_fixed(num, target=None):
            if target is None:
                target = []
            target.append(num)
            return target
        print(f"10: {append_to_fixed(1)}, {append_to_fixed(2)}, {append_to_fixed(3)}")

        # 11
        funcs = [(lambda i=i: i) for i in range(5)]
        print(f"11: {[f() for f in funcs]}")

        # 12
        import functools
        def retry(times):
            def decorator(func):
                @functools.wraps(func)
                def wrapper(*args, **kwargs):
                    for attempt in range(times):
                        try:
                            return func(*args, **kwargs)
                        except Exception as e:
                            print(f"  попытка {attempt+1}: {e}")
                    raise RuntimeError(f"все {times} попыток провалены")
                return wrapper
            return decorator
        print(f"12: декоратор retry написан")

        # 13
        class SingletonMeta(type):
            _instances = {}
            def __call__(cls, *args, **kwargs):
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
                return cls._instances[cls]

        class Database(metaclass=SingletonMeta):
            def __init__(self, url):
                self.url = url
        db1 = Database("pg://localhost")
        db2 = Database("sqlite://:memory:")
        print(f"13: db1 is db2: {db1 is db2}")

        # 14
        class ReprMeta(type):
            def __new__(mcs, name, bases, namespace):
                annotations = namespace.get("__annotations__", {})
                if annotations:
                    def make_repr(fields):
                        def __repr__(self):
                            parts = [f"{f}={getattr(self, f)!r}" for f in fields]
                            return f"{name}({', '.join(parts)})"
                        return __repr__
                    namespace["__repr__"] = make_repr(list(annotations.keys()))
                return super().__new__(mcs, name, bases, namespace)

        class User(metaclass=ReprMeta):
            name: str
            age: int
            def __init__(self, name, age):
                self.name = name
                self.age = age
        print(f"14: {User('Алиса', 25)}")

        print()
        print("=" * 60)
        print("  Все решения написаны! Сверяй по коду выше.")
        print("=" * 60)
