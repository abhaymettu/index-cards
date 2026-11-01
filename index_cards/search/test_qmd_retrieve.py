#!/usr/bin/python3
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qmd_retrieve import refs  # noqa: E402


class Refs(unittest.TestCase):
    def test_maps_dedupes_and_keeps_order(self):
        got = refs([{"file": "qmd://vault/03 Notes/Kindle setup.md?index=memeval"},
                    {"file": "qmd://session/-Users-x/abc/subagents/a.jsonl"},
                    {"file": "qmd://vault/03 Notes/Kindle setup.md?index=memeval"}])
        self.assertEqual(got, ["vault:03 Notes/Kindle setup.md", "session:-Users-x/abc/subagents/a.jsonl"])


if __name__ == "__main__":
    unittest.main()
