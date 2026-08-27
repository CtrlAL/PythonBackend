import threading
from snowflake import Snowflake

def test_unique_and_monotonic():
    s = Snowflake(node_id=1)
    ids = [s.next_id() for _ in range(10000)]
    assert len(ids) == len(set(ids)), "ids not unique"
    assert ids == sorted(ids), "ids not monotonic"

def test_thread_safety():
    s = Snowflake(node_id=2)
    out = []
    def worker():
        for _ in range(2000):
            out.append(s.next_id())
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(out) == len(set(out)), "concurrent ids collided"
