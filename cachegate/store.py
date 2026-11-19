"""Bounded in-memory store with TTL expiry and LRU eviction."""

import threading
import time
from collections import OrderedDict
from typing import Callable, Generic, Optional, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    def __init__(
        self,
        max_entries: int,
        ttl_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_entries < 1:
            raise ValueError(f"max_entries must be >= 1, got {max_entries}")
        if ttl_seconds <= 0:
            raise ValueError(f"ttl_seconds must be > 0, got {ttl_seconds}")
        self._max_entries = max_entries
        self._ttl = ttl_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._items: "OrderedDict[str, tuple[float, V]]" = OrderedDict()

    def get(self, key: str) -> Optional[V]:
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if self._clock() >= expires_at:
                del self._items[key]
                return None
            self._items.move_to_end(key)
            return value

    def put(self, key: str, value: V) -> None:
        with self._lock:
            self._items[key] = (self._clock() + self._ttl, value)
            self._items.move_to_end(key)
            while len(self._items) > self._max_entries:
                self._items.popitem(last=False)

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)
