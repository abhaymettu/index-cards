#!/usr/bin/python3
import os
import sqlite3
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fts_retrieve import fts_refs, search  # noqa: E402
from fuse import rrf  # noqa: E402


class Fuse(unittest.TestCase):
    def test_ref_in_both_lists_wins(self):
        self.assertEqual(rrf([["a:1", "b:2", "c:3"], ["c:3", "d:4"]])[:2], ["c:3", "a:1"])


class Fts(unittest.TestCase):
    def test_or_matches_and_maps_refs(self):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE documents_fts USING fts5(filepath, title, body, "
                    "tokenize='porter unicode61')")
        con.executemany("INSERT INTO documents_fts VALUES (?, '', ?)", [
            ("vault/notes/garden.md", "The tomato trellis was rebuilt with cedar posts."),
            ("session/-Users-x/a.jsonl", "bicycles " * 50),
            ("audit/kitchen.md", "Tomato soup."),
        ])
        got = fts_refs(con, 'When was the "trellis" rebuilt, and with which posts?', 10)
        self.assertEqual(got, ["vault:notes/garden.md"])
        self.assertEqual(fts_refs(con, "the and of", 10), [])

    def test_search_maps_collection_root_and_snippets(self):
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE documents_fts USING fts5(filepath, title, body, "
                    "tokenize='porter unicode61')")
        con.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, collection TEXT, path TEXT)")
        con.execute("CREATE TABLE store_collections (name TEXT, path TEXT)")
        con.execute("INSERT INTO store_collections VALUES ('vault', '/v')")
        con.execute("INSERT INTO documents VALUES (7, 'vault', 'notes/garden.md')")
        con.execute("INSERT INTO documents_fts(rowid, filepath, title, body) VALUES "
                    "(7, 'vault/notes/garden.md', '', 'The tomato trellis was rebuilt.')")
        self.assertEqual(search(con, "trellis rebuilt", 5),
                         [("/v/notes/garden.md", "The tomato [trellis] was [rebuilt].")])


if __name__ == "__main__":
    unittest.main()
