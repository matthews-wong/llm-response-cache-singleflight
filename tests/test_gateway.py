import threading
import unittest

from cachegate import CachedGateway, FakeProvider, Request, TTLCache


def gateway(provider):
    return CachedGateway(provider, TTLCache(max_entries=8, ttl_seconds=60.0))


class CachedGatewayTest(unittest.TestCase):
    def test_second_identical_request_is_a_hit(self):
        provider = FakeProvider()
        gw = gateway(provider)
        first = gw.complete(Request("m", "hi"))
        second = gw.complete(Request("m", "hi", metadata={"trace_id": "x"}))
        self.assertEqual(first, second)
        self.assertEqual(provider.calls, 1)
        self.assertEqual(gw.hits, 1)

    def test_sampled_requests_bypass_the_cache(self):
        provider = FakeProvider()
        gw = gateway(provider)
        for _ in range(3):
            gw.complete(Request("m", "hi", temperature=0.7))
        self.assertEqual(provider.calls, 3)

    def test_concurrent_duplicates_make_one_call(self):
        provider = FakeProvider(latency=0.1)
        gw = gateway(provider)
        results = []

        def work():
            results.append(gw.complete(Request("m", "same")))

        threads = [threading.Thread(target=work) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(results), 8)
        self.assertEqual(gw.coalesced + gw.hits, 7)

    def test_errors_are_shared_but_not_cached(self):
        provider = FakeProvider(latency=0.1, fail_first=1)
        gw = gateway(provider)
        errors = []

        def work():
            try:
                gw.complete(Request("m", "boom"))
            except RuntimeError as exc:
                errors.append(exc)

        threads = [threading.Thread(target=work) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(errors), 4)
        self.assertEqual(provider.calls, 1)
        # The failure was not stored, so the next request goes out again.
        self.assertEqual(gw.complete(Request("m", "boom")).text, "echo: boom")
        self.assertEqual(provider.calls, 2)


if __name__ == "__main__":
    unittest.main()
