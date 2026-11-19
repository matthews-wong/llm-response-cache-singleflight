import unittest

from cachegate.store import TTLCache


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class TTLCacheTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()

    def cache(self, max_entries=2, ttl=10.0):
        return TTLCache(max_entries, ttl, clock=self.clock)

    def test_miss_returns_none(self):
        self.assertIsNone(self.cache().get("a"))

    def test_hit_before_expiry(self):
        c = self.cache()
        c.put("a", 1)
        self.clock.now = 9.9
        self.assertEqual(c.get("a"), 1)

    def test_expires_at_ttl(self):
        c = self.cache()
        c.put("a", 1)
        self.clock.now = 10.0
        self.assertIsNone(c.get("a"))
        self.assertEqual(len(c), 0)

    def test_evicts_least_recently_used(self):
        c = self.cache(max_entries=2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")
        c.put("c", 3)
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("c"), 3)

    def test_put_refreshes_ttl(self):
        c = self.cache()
        c.put("a", 1)
        self.clock.now = 8.0
        c.put("a", 2)
        self.clock.now = 15.0
        self.assertEqual(c.get("a"), 2)

    def test_rejects_bad_config(self):
        with self.assertRaisesRegex(ValueError, "max_entries.*0"):
            TTLCache(0, 1.0)
        with self.assertRaisesRegex(ValueError, "ttl_seconds.*-1"):
            TTLCache(1, -1)


if __name__ == "__main__":
    unittest.main()
