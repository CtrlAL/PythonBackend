"""Comprehensions: list, dict, set, generator, вложенные.

Comprehensions — питоновий синтаксис для создания коллекций
одной строкой. Читабельнее циклов, быстрее (оптимизированы в CPython).

Запуск: python 04_comprehensions.py
"""

# ── 1. List comprehension ─────────────────────────────────────────

squares = [x ** 2 for x in range(10)]
print(f"квадраты:         {squares}")

evens = [x for x in range(20) if x % 2 == 0]
print(f"чётные:           {evens}")

# с условием + else
labels = ["чёт" if x % 2 == 0 else "нечёт" for x in range(6)]
print(f"метки:            {labels}")

# то же самое через обычный цикл:
# result = []
# for x in range(10):
#     result.append(x ** 2)


# ── 2. Dict comprehension ─────────────────────────────────────────

ascii_map = {chr(i): i for i in range(ord("a"), ord("g") + 1)}
print(f"буква → код:      {ascii_map}")

inverted = {v: k for k, v in ascii_map.items()}
print("инвертирован:    ", inverted)

# фильтрация словаря
scores = {"Алиса": 95, "Борис": 67, "Вика": 88, "Глеб": 42}
passed = {name: s for name, s in scores.items() if s >= 60}
print(f"сдали (≥60):      {passed}")


# ── 3. Set comprehension ──────────────────────────────────────────

words = ["hello", "world", "hello", "python", "world"]
unique_lens = {len(w) for w in words}
print(f"уникальные длины: {unique_lens}")

# для удаления дубликатов с преобразованием
nums = [1, 2, 2, 3, 3, 3, 4, 4, 4, 4]
unique_squares = {x ** 2 for x in nums}
print(f"уникальные квадраты: {sorted(unique_squares)}")


# ── 4. Generator comprehension ────────────────────────────────────
# Ленивая вычисления — элементы генерируются по одному, не хранятся в памяти

total = sum(x ** 2 for x in range(1_000_000))  # без списка в памяти
print(f"сумма квадратов 0..999999: {total:,}")

# проверка — генератор исчерпывается за один проход
gen = (x * 2 for x in range(5))
first = next(gen)
second = next(gen)
print(f"первые два из gen: {first}, {second}")
# list(gen) даст только [8, 10] — первые два уже забраны


# ── 5. Вложенные comprehension ────────────────────────────────────

# Матрица 3x3
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

# Разворачиваем в плоский список
flat = [num for row in matrix for num in row]
print(f"плоский:           {flat}")

# Транспонирование
transposed = [[row[i] for row in matrix] for i in range(3)]
print(f"транспонированная: {transposed}")

# dict comprehension из двух списков
keys = ["name", "age", "city"]
values = ["Маша", 25, "Москва"]
person = {k: v for k, v in zip(keys, values)}
print(f"person:            {person}")


# ── 6. Комбинация: вложенная + фильтрация ─────────────────────────

# Найти все пары (i, j), где i < j и оба чётные
pairs = [
    (i, j)
    for i in range(10)
    for j in range(i + 1, 10)
    if i % 2 == 0 and j % 2 == 0
]
print(f"чётные пары (i<j): {pairs[:6]}...")  # первые 6


# ── 7. Walrus operator в comprehension (Python 3.8+) ──────────────

# Без walrus: вычисляем len дважды
data = ["hello", "world", "python", "hi", "go"]

# С walrus: вычисляем один раз и используем в фильтре и в результате
result = [
    (name, length)
    for name in data
    if (length := len(name)) > 2  # walrus присваивает + проверяет
]
print(f"длинные слова:     {result}")


# ── 8. Генератор с побочным эффектом (logging/debug) ─────────────

def process(items):
    return [
        x * 2
        for x in items
        if x > 0  # пропускаем отрицательные
        # можно добавить print(x) для отладки:
        # for x in items if (print(f"  check: {x}") or True)
    ]

print(f"обработка:         {process([-2, -1, 0, 1, 2, 3])}")


# ── 9. Сравнение: comprehension vs цикл vs map/filter ────────────

import timeit

data = list(range(10_000))

# Способ 1: цикл
def with_loop():
    result = []
    for x in data:
        if x % 2 == 0:
            result.append(x ** 2)
    return result

# Способ 2: comprehension
def with_comp():
    return [x ** 2 for x in data if x % 2 == 0]

# Способ 3: map + filter + lambda
def with_map():
    return list(map(lambda x: x ** 2, filter(lambda x: x % 2 == 0, data)))

t_loop = timeit.timeit(with_loop, number=100)
t_comp = timeit.timeit(with_comp, number=100)
t_map = timeit.timeit(with_map, number=100)

print(f"\nбенчмарк 10K элементов × 100 итераций:")
print(f"  цикл:          {t_loop:.4f} сек")
print(f"  comprehension: {t_comp:.4f} сек  ({t_loop/t_comp:.1f}x быстрее цикла)")
print(f"  map+filter:    {t_map:.4f} сек")


# ── 10. Readability: плохая vs хорошая comprehension ──────────────

# ПЛОХО: слишком длинная, нечитабельно
# bad = [f"{x}: {y}" for x in range(10) for y in range(10) if x != y and x < 5 and y > 3]

# ХОРОШО: разбиваем на этапы
x_range = range(5)
y_range = range(10)
pairs_good = [(x, y) for x in x_range for y in y_range if x != y and y > 3]
result_good = [f"{x}: {y}" for x, y in pairs_good]
print(f"\nreadable pairs:   {result_good[:5]}...")
