"""Seeded load simulation: how many provider calls does the cache save?

Runs against the fake provider, so the numbers describe this simulated workload
only (not any real model or traffic).
"""

import random
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cachegate import CachedGateway, FakeProvider, Request, TTLCache  # noqa: E402

SEED = 7
REQUESTS = 400
DISTINCT_PROMPTS = 25
WORKERS = 8
PROVIDER_LATENCY = 0.005


def main() -> None:
    rng = random.Random(SEED)
    # Skewed draw: a few prompts are asked far more often than the rest.
    prompts = [f"question {min(int(rng.expovariate(0.2)), DISTINCT_PROMPTS - 1)}" for _ in range(REQUESTS)]
    provider = FakeProvider(latency=PROVIDER_LATENCY)
    gateway = CachedGateway(provider, TTLCache(max_entries=64, ttl_seconds=300.0))

    def worker(chunk):
        for prompt in chunk:
            gateway.complete(Request("fake-model", prompt))

    chunks = [prompts[i::WORKERS] for i in range(WORKERS)]
    threads = [threading.Thread(target=worker, args=(c,)) for c in chunks]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    distinct = len(set(prompts))
    print(f"workload: {REQUESTS} requests, {distinct} distinct prompts, seed {SEED}, {WORKERS} threads")
    print(f"provider calls: {provider.calls}")
    print(f"cache hits: {gateway.hits}, coalesced: {gateway.coalesced}")
    if provider.calls != distinct:
        raise SystemExit(f"expected one provider call per distinct prompt ({distinct}), got {provider.calls}")


if __name__ == "__main__":
    main()
