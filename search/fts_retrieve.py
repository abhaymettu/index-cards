#!/usr/bin/python3
"""OR-BM25 over qmd's FTS5 table.

  fts_retrieve.py DB [--n 10]             memeval --cmd adapter: question on stdin, ranked refs out
  fts_retrieve.py DB [--n 10] WORDS...    search: absolute path and a snippet per hit
  DB: a qmd index, e.g. ~/.cache/qmd/<index>.sqlite

`qmd search` ANDs every term, so a natural-language question usually matches nothing. This ORs the
same content terms memeval's rg arm uses and ranks by FTS5 bm25(), which normalises for length.
Runs SELECTs only (a WAL-mode db will not open with mode=ro). qmd's `filepath` column is
`<collection>/<path>`, mapped to `<collection>:<path>`.
"""
import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval"))
from memeval import terms  # noqa: E402


def match(question):
    return " OR ".join('"%s"' % t.replace('"', '""') for t in terms(question))


def fts_refs(con, question, n):
    q = match(question)
    if not q:
        return []
    rows = con.execute("SELECT filepath FROM documents_fts WHERE documents_fts MATCH ? "
                       "ORDER BY bm25(documents_fts) LIMIT ?", (q, n))
    return [fp.replace("/", ":", 1) for (fp,) in rows]


def search(con, words, n):
    """(absolute path, snippet) per hit; qmd keeps documents.id == documents_fts.rowid."""
    q = match(words)
    if not q:
        return []
    roots = dict(con.execute("SELECT name, path FROM store_collections"))
    rows = con.execute("SELECT d.collection, d.path, snippet(documents_fts, 2, '[', ']', ' ... ', 16) "
                       "FROM documents_fts JOIN documents d ON d.id = documents_fts.rowid "
                       "WHERE documents_fts MATCH ? ORDER BY bm25(documents_fts) LIMIT ?", (q, n))
    return [(os.path.join(roots[c], p), " ".join(s.split())) for c, p, s in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("db")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("words", nargs="*")
    args = ap.parse_intermixed_args()
    con = sqlite3.connect(os.path.expanduser(args.db))
    if args.words:
        for path, snip in search(con, " ".join(args.words), args.n):
            print("%s\n    %s" % (path, snip))
    else:
        print("\n".join(fts_refs(con, sys.stdin.read(), args.n)))


if __name__ == "__main__":
    main()
