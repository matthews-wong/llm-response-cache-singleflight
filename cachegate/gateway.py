"""Cache in front of a provider, with single-flight for concurrent duplicates."""

import threading
from typing import Dict, Optional

from .keys import request_key
from .provider import Provider, Request, Response
from .store import TTLCache


class _Flight:
    def __init__(self) -> None:
        self.done = threading.Event()
        self.response: Optional[Response] = None
        self.error: Optional[BaseException] = None


class CachedGateway:
    def __init__(self, provider: Provider, cache: TTLCache[Response]) -> None:
        self._provider = provider
        self._cache = cache
        self._lock = threading.Lock()
        self._inflight: Dict[str, _Flight] = {}
        self.hits = 0
        self.coalesced = 0
        self.provider_calls = 0

    def complete(self, request: Request) -> Response:
        # A sampled answer is not reproducible, so reusing it would be wrong.
        if request.temperature != 0:
            return self._call(request)

        key = request_key(request)
        cached = self._cache.get(key)
        if cached is not None:
            with self._lock:
                self.hits += 1
            return cached

        with self._lock:
            flight = self._inflight.get(key)
            leader = flight is None
            if leader:
                flight = self._inflight[key] = _Flight()
            else:
                self.coalesced += 1

        if not leader:
            flight.done.wait()
            if flight.error is not None:
                raise flight.error
            return flight.response

        try:
            flight.response = self._call(request)
            self._cache.put(key, flight.response)
            return flight.response
        except BaseException as exc:
            flight.error = exc
            raise
        finally:
            # Drop the flight before waking waiters so a retry starts fresh.
            with self._lock:
                del self._inflight[key]
            flight.done.set()

    def _call(self, request: Request) -> Response:
        with self._lock:
            self.provider_calls += 1
        return self._provider.complete(request)
