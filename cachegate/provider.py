"""Provider seam: every model call goes through ``Provider.complete``."""

import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol


@dataclass(frozen=True)
class Request:
    model: str
    prompt: str
    temperature: float = 0.0
    max_tokens: int = 256
    # Tracing data that must not change the cache key.
    metadata: dict = field(default_factory=dict, compare=False)


@dataclass(frozen=True)
class Response:
    text: str
    model: str


class Provider(Protocol):
    def complete(self, request: Request) -> Response: ...


class FakeProvider:
    """Deterministic provider: the answer is a pure function of the request."""

    def __init__(self, latency: float = 0.0, fail_first: int = 0) -> None:
        self._latency = latency
        self._fail_first = fail_first
        self._lock = threading.Lock()
        self.calls = 0

    def complete(self, request: Request) -> Response:
        with self._lock:
            self.calls += 1
            should_fail = self.calls <= self._fail_first
        if self._latency:
            time.sleep(self._latency)
        if should_fail:
            raise RuntimeError(f"fake provider failure for model {request.model!r}")
        return Response(text=f"echo: {request.prompt}", model=request.model)
