import time
import threading

EPOCH_MILLISECONDS = 1288834974657  # Twitter epoch

class Snowflake:
    def __init__(self, node_id=1):
        self.node_id = node_id & 0x3FF
        self.lock = threading.Lock()
        self.sequence = 0
        self.last_timestamp = 0

    def _current_timestamp(self):
        return int(time.time() * 1000) - EPOCH_MILLISECONDS

    def next_id(self):
        with self.lock:
            timestamp = self._current_timestamp()
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF
                if self.sequence == 0:
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_timestamp()
            else:
                self.sequence = 0
            self.last_timestamp = timestamp
            return ((timestamp << 22) | (self.node_id << 12) | self.sequence)
