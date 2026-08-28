# app/infrastructure/id_generator.py
import threading
import time

EPOCH_MILLISECONDS = 1288834974657


class SnowflakeIdGenerator:
    def __init__(self, node_id: int = 1) -> None:
        self._node_id = node_id & 0x3FF
        self._lock = threading.Lock()
        self._sequence = 0
        self._last_timestamp = 0

    def _current_timestamp(self) -> int:
        return int(time.time() * 1000) - EPOCH_MILLISECONDS

    def generate(self) -> int:
        with self._lock:
            timestamp = self._current_timestamp()

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & 0xFFF

                if self._sequence == 0:

                    while timestamp <= self._last_timestamp:
                        timestamp = self._current_timestamp()
            else:
                self._sequence = 0

            self._last_timestamp = timestamp

            return (timestamp << 22) | (self._node_id << 12) | self._sequence
