"""Tricky Questions: ловушки и подводные камни Python.

Каждый пример: код → проблема → объяснение → решение.
Запуск: python 05_tricky.py
"""


# ══════════════════════════════════════════════════════════════════
# 1. ПОДСТАВА В ЦИКЛЕ: все ссылки на одну переменную
# ══════════════════════════════════════════════════════════════════

def problem_mutable_default():
    """ПРОБЛЕМА: мутабельный default argument."""
    def append_to(num, target=[]):
        target.append(num)
        return target

    print(append_to(1))  # [1]
    print(append_to(2))  # [1, 2] — ожидаем [2]!
    print(append_to(3))  # [1, 2, 3] — ожидаем [3]!

    # Default argument вычисляется ОДИН раз при определении функции,
    # а не при каждом вызове. Список [] создаётся один раз и переиспользуется.

def solution_mutable_default():
    """РЕШЕНИЕ: использовать None как маркер."""
    def append_to(num, target=None):
        if target is None:
            target = []
        target.append(num)
        return target

    print(append_to(1))  # [1]
    print(append_to(2))  # [2] — работает!
    print(append_to(3))  # [3]


# ══════════════════════════════════════════════════════════════════
# 2. LATE BINDING closures
# ══════════════════════════════════════════════════════════════════

def problem_late_binding():
    """ПРОБЛЕМА: замыкания захватывают ПЕРЕМЕННУЮ, а не значение."""
    funcs = []
    for i in range(5):
        funcs.append(lambda: i)

    print([f() for f in funcs])  # [4, 4, 4, 4, 4] — ожидаем [0, 1, 2, 3, 4]

    # Все lambda ссылаются на одну переменную i.
    # К моменту вызова i = 4, и все функции возвращают 4.

def solution_late_binding():
    """РЕШЕНИЕ: захватить значение через default argument."""
    funcs = []
    for i in range(5):
        funcs.append(lambda i=i: i)  # i=i захватывает текущее значение

    print([f() for f in funcs])  # [0, 1, 2, 3, 4]

    # Альтернатива: functools.partial
    from functools import partial
    funcs2 = [partial(lambda x: x, i) for i in range(5)]
    print([f() for f in funcs2])  # [0, 1, 2, 3, 4]


# ══════════════════════════════════════════════════════════════════
# 3. ПРЕДАЧА СПИСКА В КОНСТРУКТОР
# ══════════════════════════════════════════════════════════════════

def problem_class_mutable():
    """ПРОБЛЕМА: все экземпляры делят один список."""
    class Bug:
        def __init__(self, items=[]):
            self.items = items

    a = Bug()
    b = Bug()
    a.items.append("x")
    print(f"a.items: {a.items}")  # ['x']
    print(f"b.items: {b.items}")  # ['x'] — b.items = a.items!

def solution_class_mutable():
    """РЕШЕНИЕ: None + init."""
    class Fix:
        def __init__(self, items=None):
            self.items = items if items is not None else []

    a = Fix()
    b = Fix()
    a.items.append("x")
    print(f"a.items: {a.items}")  # ['x']
    print(f"b.items: {b.items}")  # [] — независимый список


# ══════════════════════════════════════════════════════════════════
# 4. FLOAT ТОЧНОСТЬ
# ══════════════════════════════════════════════════════════════════

def problem_float():
    """ПРОБЛЕМА: 0.1 + 0.2 != 0.3"""
    print(f"0.1 + 0.2 = {0.1 + 0.2}")       # 0.30000000000000004
    print(f"0.1 + 0.2 == 0.3: {0.1 + 0.2 == 0.3}")  # False

    # IEEE 754: 0.1 не представим точно в двоичном формате,
    # как 1/3 не представимо точно в десятичном.

def solution_float():
    """РЕШЕНИЕ: decimal или round."""
    from decimal import Decimal, getcontext
    getcontext().prec = 10

    a = Decimal("0.1") + Decimal("0.2")
    print(f"Decimal: {a} == Decimal('0.3'): {a == Decimal('0.3')}")  # True

    # Или round для быстрой проверки
    print(f"round:   {round(0.1 + 0.2, 10) == 0.3}")  # True

    # Для денег: целые копейки, не float
    price_kopeks = 1500  # 15.00 руб
    print(f"копейки:  {price_kopeks}")


# ══════════════════════════════════════════════════════════════════
# 5. GIL: threading vs multiprocessing
# ══════════════════════════════════════════════════════════════════

def problem_gil():
    """ПРОБЛЕМА: потоки НЕ ускоряют CPU-bound задачи."""
    import threading
    import time

    counter = 0

    def count(n):
        nonlocal counter
        for _ in range(n):
            counter += 1

    n = 5_000_000

    # Однопоточный
    t0 = time.perf_counter()
    count(n)
    count(n)
    t1 = time.perf_counter()
    one_thread = t1 - t0

    # Двухпоточный
    counter = 0
    t0 = time.perf_counter()
    t1 = threading.Thread(target=count, args=(n,))
    t2 = threading.Thread(target=count, args=(n,))
    t1.start(); t2.start()
    t1.join(); t2.join()
    t1 = time.perf_counter()
    two_threads = t1 - t0

    print(f"  1 поток:  {one_thread:.2f} сек")
    print(f"  2 потока: {two_threads:.2f} сек  (GIL: не быстрее!)")

    # GIL не даёт потокам работать одновременно в CPython.
    # Для CPU-bound используй multiprocessing.


# ══════════════════════════════════════════════════════════════════
# 6. YIELD и генератор: исчерпание
# ══════════════════════════════════════════════════════════════════

def problem_generator_exhaustion():
    """ПРОБЛЕМА: генератор можно пройти только один раз."""
    def my_gen():
        yield 1
        yield 2
        yield 3

    g = my_gen()
    print(f"первый проход:  {list(g)}")   # [1, 2, 3]
    print(f"второй проход:  {list(g)}")   # [] — пусто!

    # Генератор «исчерпан» после первого прохода.

def solution_generator_exhaustion():
    """РЕШЕНИЕ: обернуть в функцию-фабрику."""
    def my_gen_factory():
        def gen():
            yield 1
            yield 2
            yield 3
        return gen

    factory = my_gen_factory()
    print(f"первый:  {list(factory())}")  # [1, 2, 3]
    print(f"второй:  {list(factory())}")  # [1, 2, 3]

    # Или itertools.tee для разветвления
    import itertools
    g = (x for x in [1, 2, 3])
    a, b = itertools.tee(g, 2)
    print(f"tee a:   {list(a)}")
    print(f"tee b:   {list(b)}")


# ══════════════════════════════════════════════════════════════════
# 7. UNPACKING: звёздочка и tuple
# ══════════════════════════════════════════════════════════════════

def problem_unpacking():
    """ПРОБЛЕМА: star unpacking только с Iterable, не с int."""
    a, *b, c = [1, 2, 3, 4, 5]
    print(f"a={a}, b={b}, c={c}")  # a=1, b=[2,3,4], c=5

    # А если попробовать:
    # a, *b, c = 12345  # TypeError: cannot unpack non-iterable int

def solution_unpacking():
    """РЕШЕНИЕ: понимать, где что работает."""
    # Список/строка — ок
    first, *middle, last = "hello"
    print(f"first={first}, middle={middle}, last={last}")

    # В функциях — star args
    def func(a, b, *args, **kwargs):
        print(f"a={a}, b={b}, args={args}, kwargs={kwargs}")

    func(1, 2, 3, 4, x=5)  # args=(3,4), kwargs={'x': 5}


# ══════════════════════════════════════════════════════════════════
# 8. STRING interning и сравнение
# ══════════════════════════════════════════════════════════════════

def problem_string_interning():
    """ПРОБЛЕМА: == и is — разные вещи для строк."""
    a = "hello"
    b = "hello"
    c = "hel" + "lo"
    d = "hello!"
    e = d[:-1]

    print(f"a == b: {a == b}")  # True — содержимое совпадает
    print(f"a is b: {a is b}")  # True — CPython interning (оптимизация)
    print(f"a is c: {a is c}")  # True — тоже interning
    print(f"a is e: {a is e}")  # False — e создана динамически

    # Всегда используй == для сравнения строк, never is.

def solution_string_interning():
    """РЕШЕНИЕ: == для значений, is для None/синглтонов."""
    name = input if False else "hello"  # избегаем input()

    # Правильно
    if name == "hello":
        print("привет!")

    # Неправильно (может работать, но ненадёжно)
    # if name is "hello": ...

    # is подходит ТОЛЬКО для
    x = None
    if x is None:
        print("x is None — OK")


# ══════════════════════════════════════════════════════════════════
# 9. LIST SORIGIN: shallow copy vs deep copy
# ══════════════════════════════════════════════════════════════════

def problem_shallow_copy():
    """ПРОБЛЕМА: поверхносточная копия не копирует вложенные объекты."""
    original = [[1, 2], [3, 4]]
    shallow = original.copy()  # или original[:] или list(original)

    shallow[0][0] = 99
    print(f"original: {original}")  # [[99, 2], [3, 4]] — original тоже изменился!
    print(f"shallow:  {shallow}")

    # .copy() копирует ссылки, а не сами вложенные списки.

def solution_deep_copy():
    """РЕШЕНИЕ: copy.deepcopy для вложенных структур."""
    import copy

    original = [[1, 2], [3, 4]]
    deep = copy.deepcopy(original)

    deep[0][0] = 99
    print(f"original: {original}")  # [[1, 2], [3, 4]] — не изменился!
    print(f"deep:     {deep}")

    # Для одномерных список浅копия достаточна.
    # Для вложенных — deepcopy.


# ══════════════════════════════════════════════════════════════════
# 10. ДЕКОРАТОР С АРГУМЕНТАМИ: тройное замыкание
# ══════════════════════════════════════════════════════════════════

def problem_decorator_args():
    """ПРОБЛЕМА: декоратор с аргументами — 3 уровня вложенности."""
    import functools

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

    @retry(times=3)
    def flaky():
        import random
        if random.random() < 0.7:
            raise ValueError("случайная ошибка")
        return "успех!"

    result = flaky()
    print(f"  результат: {result}")

    # Схема: @retry(times=3) → retry(3) → decorator → wrapper
    # retry(times=3) возвращает decorator
    # decorator(func) возвращает wrapper
    # @decorator заменяет func на wrapper


# ══════════════════════════════════════════════════════════════════
# 11. ENUM: auto() и comparison
# ══════════════════════════════════════════════════════════════════

def problem_enum():
    """ПРОБЛЕМА: Enum и сравнение."""
    from enum import Enum, auto

    class Color(Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    print(f"RED == 1: {Color.RED == 1}")    # False — разные типы
    print(f"RED.value == 1: {Color.RED.value == 1}")  # True

    # Enum члены нельзя сравнивать друг с другом
    # Color.RED < Color.GREEN  # TypeError


# ══════════════════════════════════════════════════════════════════
# 12. WALRUS OPERATOR (Python 3.8+)
# ══════════════════════════════════════════════════════════════════

def demo_walrus():
    """ walrus := позволяет присваивать внутри выражения."""
    import re

    text = "contact: user@example.com, admin@test.org"

    # Без walrus: вызываем regex дважды
    match = re.search(r"[\w.]+@[\w.]+", text)
    if match:
        email = match.group()
    print(f"без walrus: {email}")

    # С walrus: одна строка
    if m := re.search(r"[\w.]+@[\w.]+", text):
        print(f"с walrus:  {m.group()}")

    # В comprehension
    data = [1, -2, 3, -4, 5]
    results = [(x, x**2) for x in data if (squared := x**2) > 4]
    print(f"walrus в comp: {results}")


# ══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    demos = [
        ("1. Mutable default argument",    problem_mutable_default,    solution_mutable_default),
        ("2. Late binding closures",       problem_late_binding,       solution_late_binding),
        ("3. Class mutable default",       problem_class_mutable,      solution_class_mutable),
        ("4. Float точность",              problem_float,              solution_float),
        ("5. GIL: threads vs CPU-bound",   problem_gil,                None),
        ("6. Generator exhaustion",        problem_generator_exhaustion, solution_generator_exhaustion),
        ("7. Unpacking",                   problem_unpacking,          solution_unpacking),
        ("8. String interning",            problem_string_interning,   solution_string_interning),
        ("9. Shallow vs deep copy",        problem_shallow_copy,       solution_deep_copy),
        ("10. Декоратор с аргументами",    problem_decorator_args,     None),
        ("11. Enum comparison",            problem_enum,               None),
        ("12. Walrus operator",            demo_walrus,                None),
    ]

    for title, problem, solution in demos:
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")

        print("\n  --- проблема / демонстрация ---")
        problem()

        if solution:
            print("\n  --- решение ---")
            solution()
