# llm-response-cache-singleflight

An in-process response cache for LLM calls, written with the standard library only.

Two things it does that a plain dict does not:

- **Canonical keys.** Two requests that mean the same thing hash to the same key,
  whatever the order of their fields. Fields that do not change the answer
  (request ids, tracing metadata) are left out of the key.
- **Single-flight.** If ten threads ask the same question while the first call is
  still running, one provider call is made and all ten get its result.

Everything goes through a small `Provider` interface. A deterministic fake provider
ships with the repo, so nothing here needs a network or an API key.

## Design decisions

- Only deterministic requests (`temperature == 0`) are cached by default. Caching a
  sampled answer would quietly turn a random generator into a constant.
- Errors are never cached. A waiting caller sees the same error as the leader, and
  the next request tries again.
- Entries expire after a TTL and the store is bounded with LRU eviction.

## Layout

    cachegate/   library
    tests/       unittest suite
    scripts/     seeded simulation

## Validate

    make validate

Runs the unit tests and the simulation.

The simulation replays 400 seeded requests over 23 distinct prompts on 8 threads
against the fake provider. With the cache, the provider is called 23 times, once
per distinct prompt. That figure comes from this fixture workload, not from real
traffic or a real model.

## Usage

    from cachegate import CachedGateway, FakeProvider, Request, TTLCache

    gateway = CachedGateway(FakeProvider(), TTLCache(max_entries=1024, ttl_seconds=300))
    print(gateway.complete(Request("model", "hello")).text)

Swap `FakeProvider` for any object with a `complete(request) -> Response` method.
