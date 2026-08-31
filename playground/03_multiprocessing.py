"""Мультипроцессы: CPU-bound задачи, пул, shared memory.

Каждый процесс — свой интерпретатор Python, обходит GIL.
Идеально для числовых вычислений, обработки изображений и т.д.

Запуск: python 03_multiprocessing.py
"""

import multiprocessing as mp
import os
import time
from multiprocessing import Pool, Value, Array
from dataclasses import dataclass


# ── 1. Базовый: Pool для CPU-bound задачи ──────────────────────────

def heavy_compute(n: int) -> int:
    """Тяжёлое вычисление: сумма квадратов (CPU-bound)."""
    return sum(i * i for i in range(n))


def demo_pool() -> None:
    data = [10_000_000] * 4

    start = time.perf_counter()
    result_seq = [heavy_compute(x) for x in data]
    seq_time = time.perf_counter() - start

    start = time.perf_counter()
    with Pool(processes=4) as pool:
        result_par = pool.map(heavy_compute, data)
    par_time = time.perf_counter() - start

    print(f"  последовательно: {seq_time:.2f} сек")
    print(f"  4 процесса:     {par_time:.2f} сек")
    print(f"  ускорение:       {seq_time / par_time:.1f}x")
    assert result_seq == result_par, "результаты не совпадают"


# ── 2. Process + shared memory (Array, Value) ─────────────────────

def shared_increment(shared_array: Array, index: int, value: int) -> None:
    """Каждый процесс пишет в общий массив через lock."""
    with shared_array.get_lock():
        shared_array[index] += value


def demo_shared_memory() -> None:
    shared = Array("i", [0, 0, 0, 0])  # 4 целых числа

    processes = []
    for i in range(4):
        p = mp.Process(target=shared_increment, args=(shared, i, 100))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    print(f"  массив после 4 процессов: {list(shared)}")
    print(f"  ожидается: [100, 100, 100, 100]")


# ── 3. Process + Pipe: обмен данными ──────────────────────────────

def sender(conn: mp.Connection, data: list) -> None:
    """Отправляет данные через Pipe."""
    for item in data:
        conn.send(item)
    conn.send(None)  # сигнал завершения


def receiver(conn: mp.Connection) -> list:
    """Принимает данные через Pipe и обрабатывает."""
    results = []
    while True:
        msg = conn.recv()
        if msg is None:
            break
        results.append(msg * 2)
    return results


def demo_pipe() -> None:
    parent_conn, child_conn = mp.Pipe()

    data = list(range(1, 11))

    p_sender = mp.Process(target=sender, args=(parent_conn, data))
    p_receiver = mp.Process(target=receiver, args=(child_conn,))

    p_sender.start()
    p_receiver.start()

    p_sender.join()
    p_receiver.join()

    # Результат уже обработан в receiver (не через return — так_PID)
    # Для получения результата используем Queue или shared memory.
    # Здесь просто демонстрируем передачу.
    print(f"  отправлено: {data}")
    print(f"  receiver обработал (x*2) и завершился")


# ── 4. Queue: producer-consumer ───────────────────────────────────

def producer(queue: mp.Queue, n: int) -> None:
    """Кладёт числа в очередь."""
    for i in range(n):
        queue.put(i * i)
    queue.put(None)  # стоп-сигнал


def consumer(queue: mp.Queue, results: list) -> None:
    """Достаёт из очереди и суммирует."""
    total = 0
    while True:
        item = queue.get()
        if item is None:
            break
        total += item
    results.append(total)


def demo_queue() -> None:
    queue = mp.Queue()
    manager = mp.Manager()
    results = manager.list()

    p_prod = mp.Process(target=producer, args=(queue, 100))
    p_cons = mp.Process(target=consumer, args=(queue, results))

    p_prod.start()
    p_cons.start()

    p_prod.join()
    p_cons.join()

    print(f"  сумма квадратов 0..99: {results[0]}")
    expected = sum(i * i for i in range(100))
    print(f"  ожидается:            {expected}")


# ── 5. Вложенная функция как target ───────────────────────────────

def demo_process_target() -> None:
    """Процесс может запускать вложенную функцию ( closure )."""

    def worker(shared_value: Value, delta: int) -> None:
        with shared_value.get_lock():
            shared_value.value += delta

    val = Value("i", 0)

    processes = [
        mp.Process(target=worker, args=(val, 10)),
        mp.Process(target=worker, args=(val, 20)),
        mp.Process(target=worker, args=(val, 30)),
    ]

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    print(f"  итог: {val.value} (ожидаем 60)")


# ── Запуск ────────────────────────────────────────────────────────

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)  # кроссплатформенность

    print("=" * 50)
    print("1. Pool: CPU-bound параллелизм")
    print("=" * 50)
    demo_pool()

    print("\n" + "=" * 50)
    print("2. Shared Memory (Array)")
    print("=" * 50)
    demo_shared_memory()

    print("\n" + "=" * 50)
    print("3. Pipe: передача данных")
    print("=" * 50)
    demo_pipe()

    print("\n" + "=" * 50)
    print("4. Queue: producer-consumer")
    print("=" * 50)
    demo_queue()

    print("\n" + "=" * 50)
    print("5. Вложенная функция как target")
    print("=" * 50)
    demo_process_target()
