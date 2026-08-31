"""Многопоточность — I/O-bound задачи.

Python GIL не даёт потокам распараллелить CPU-bound код,
но для I/O (сеть, файлы, БД) потоки работают отлично.

Запуск: python 01_threading.py
"""

import concurrent.futures
import threading
import time


# ── 1. Базовый пример: потоки с lock ──────────────────────────────

counter = 0
lock = threading.Lock()


def increment(n: int) -> None:
    global counter
    for _ in range(n):
        with lock:
            counter += 1


def demo_lock() -> None:
    """Без lock的竞争条件: итог < 2_000_000.
    С lock — ровно 2_000_000."""
    global counter
    counter = 0

    t1 = threading.Thread(target=increment, args=(1_000_000,))
    t2 = threading.Thread(target=increment, args=(1_000_000,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print(f"[lock]  итог: {counter:,} (ожидаем 2,000,000)")


# ── 2. ThreadPoolExecutor: I/O-bound задачи ───────────────────────

def fake_io_request(url: str) -> str:
    """Эмулирует запрос к API (сон 0.5 сек)."""
    time.sleep(0.5)
    return f"данные из {url}"


def demo_executor() -> None:
    urls = [
        "https://api.example.com/users",
        "https://api.example.com/posts",
        "https://api.example.com/comments",
        "https://api.example.com/likes",
    ]

    start = time.perf_counter()

    # Последовательно — 4 × 0.5 = 2 сек
    results_seq = [fake_io_request(u) for u in urls]
    seq_time = time.perf_counter() - start

    start = time.perf_counter()

    # В пуле потоков — ~0.5 сек (параллельно)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results_par = list(pool.map(fake_io_request, urls))
    par_time = time.perf_counter() - start

    print(f"\n[executor] последовательно: {seq_time:.2f} сек")
    print(f"[executor] параллельно:    {par_time:.2f} сек")
    print(f"[executor] ускорение:      {seq_time / par_time:.1f}x")


# ── 3. Потоки vs Event: производительность ────────────────────────

def demo_event() -> None:
    """Event позволяет потокам дождаться сигнала."""
    event = threading.Event()

    def waiter(name: str) -> None:
        print(f"  {name}: жду сигнал...")
        event.wait()
        print(f"  {name}: получил сигнал!")

    threads = [
        threading.Thread(target=waiter, args=(f"поток-{i}",))
        for i in range(3)
    ]

    for t in threads:
        t.start()

    time.sleep(0.3)
    print("  main: посылаю сигнал")
    event.set()

    for t in threads:
        t.join()


# ── Запуск ────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("1. Lock: гонка потоков")
    print("=" * 50)
    demo_lock()

    print("\n" + "=" * 50)
    print("2. ThreadPoolExecutor: I/O параллелизм")
    print("=" * 50)
    demo_executor()

    print("\n" + "=" * 50)
    print("3. Event: синхронизация потоков")
    print("=" * 50)
    demo_event()
