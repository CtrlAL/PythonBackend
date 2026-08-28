import threading
import time

EPOCH_MILLISECONDS = 1288834974657

TIMESTAMP_BITS = 41
NODE_BITS = 10
SEQUENCE_BITS = 12

NODE_SHIFT = SEQUENCE_BITS
TIMESTAMP_SHIFT = SEQUENCE_BITS + NODE_BITS

SEQUENCE_MASK = (1 << SEQUENCE_BITS) - 1
NODE_MASK = (1 << NODE_BITS) - 1


class SnowflakeIdGenerator:
    def __init__(self, node_id: int = 0) -> None:
        self._node_id = node_id & NODE_MASK
        self._lock = threading.Lock()
        self._last_timestamp = -1
        self._sequence = 0

    def _now_millis(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last: int) -> int:
        timestamp = self._now_millis()

        while timestamp <= last:
            timestamp = self._now_millis()

        return timestamp

    def generate(self) -> int:
        with self._lock:
            timestamp = self._now_millis()

            if timestamp < self._last_timestamp:
                raise RuntimeError("clock moved backwards")

            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & SEQUENCE_MASK

                if self._sequence == 0:
                    timestamp = self._wait_next_millis(self._last_timestamp)
            else:
                self._sequence = 0

            self._last_timestamp = timestamp

            return (
                ((timestamp - EPOCH_MILLISECONDS) << TIMESTAMP_SHIFT)
                | (self._node_id << NODE_SHIFT)
                | self._sequence
            )
