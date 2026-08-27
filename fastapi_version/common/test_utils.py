# fastapi_version/common/test_utils.py
import threading
from snowflake import Snowflake
from base62 import encode, decode

def test_snowflake_unique_monotonic():
    s = Snowflake(node_id=1)
    ids = [s.next_id() for _ in range(10000)]
    assert len(ids) == len(set(ids))
    assert ids == sorted(ids)

def test_snowflake_threads():
    s = Snowflake(node_id=3)
    out = []
    def w():
        for _ in range(2000): out.append(s.next_id())
    ts = [threading.Thread(target=w) for _ in range(4)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert len(out) == len(set(out))

def test_base62_roundtrip():
    for n in [0, 1, 42, 2**40, 2**62]:
        assert decode(encode(n)) == n
