import unittest

from cachegate import Request
from cachegate.keys import request_key


class RequestKeyTest(unittest.TestCase):
    def test_same_request_same_key(self):
        self.assertEqual(request_key(Request("m", "hi")), request_key(Request("m", "hi")))

    def test_metadata_does_not_change_key(self):
        a = Request("m", "hi", metadata={"trace_id": "1"})
        b = Request("m", "hi", metadata={"trace_id": "2"})
        self.assertEqual(request_key(a), request_key(b))

    def test_each_answer_deciding_field_changes_key(self):
        base = request_key(Request("m", "hi"))
        for other in (
            Request("n", "hi"),
            Request("m", "ho"),
            Request("m", "hi", temperature=0.5),
            Request("m", "hi", max_tokens=8),
        ):
            self.assertNotEqual(base, request_key(other), other)

    def test_integer_and_float_temperature_match(self):
        self.assertEqual(
            request_key(Request("m", "hi", temperature=0)),
            request_key(Request("m", "hi", temperature=0.0)),
        )

    def test_key_is_versioned(self):
        self.assertTrue(request_key(Request("m", "hi")).startswith("v1:"))


if __name__ == "__main__":
    unittest.main()
