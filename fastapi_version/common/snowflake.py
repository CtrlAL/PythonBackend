# fastapi_version/common/snowflake.py
import time, threading
EPOCH_MS = 1288834974657
class Snowflake:
    def __init__(self, node_id=1):
        self.node_id = node_id & 0x3FF
        self.lock = threading.Lock()
        self.seq = 0
        self.last_ts = 0
    def _ts(self):
        return int(time.time() * 1000) - EPOCH_MS
    def next_id(self):
        with self.lock:
            ts = self._ts()
            if ts == self.last_ts:
                self.seq = (self.seq + 1) & 0xFFF
                if self.seq == 0:
                    while ts <= self.last_ts:
                        ts = self._ts()
            else:
                self.seq = 0
            self.last_ts = ts
            return ((ts << 22) | (self.node_id << 12) | self.seq)
