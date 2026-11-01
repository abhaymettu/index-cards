#!/usr/bin/env python3
"""Fixture tests for memeval. Run: /usr/bin/python3 eval/test_memeval.py"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memeval  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        n = os.path.join(self.tmp, "notes")
        write(os.path.join(n, "garden.md"), "The tomato trellis was rebuilt with cedar posts in May.\n")
        write(os.path.join(n, "kitchen.md"), "Tomato soup recipe. Tomato tomato tomato.\n")
        write(os.path.join(n, "misc.md"), "Unrelated text about bicycles.\n")
        write(os.path.join(n, "secret/keys.md"), "tomato trellis cedar posts rebuilt\n")
        write(os.path.join(n, "image.txt"), "tomato trellis cedar\n")
        l = os.path.join(self.tmp, "logs")
        write(os.path.join(l, "day.jsonl"), '{"text": "chose cedar over pine for the trellis"}\n')
        self.corpora = {
            "notes": {"root": n, "include": ["*.md"], "exclude": ["secret/**"]},
            "logs": {"root": l, "include": ["*.jsonl"], "exclude": []},
        }
        self.corpora_path = os.path.join(self.tmp, "corpora.json")
        write(self.corpora_path, json.dumps(self.corpora))
        self.q = os.path.join(self.tmp, "questions.jsonl")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def rec(self, **kw):
        r = {"id": "q1", "category": "single", "question": "What wood holds up the trellis?",
             "answer": "Cedar posts.", "keys": ["cedar"], "gold": ["notes:garden.md"],
             "as_of": "2026-10-03", "split": "frozen", "note": ""}
        r.update(kw)
        return r

    def save(self, *recs):
        write(self.q, "".join(json.dumps(r) + "\n" for r in recs))


class Retrieval(Base):
    def test_rg_ranks_distinctive_match_first(self):
        refs = memeval.rg_retrieve("When was the tomato trellis rebuilt?", self.corpora, 5)
        self.assertEqual(refs[0], "notes:garden.md")

    def test_excludes_and_include_globs_hold(self):
        refs = memeval.rg_retrieve("tomato trellis cedar posts rebuilt", self.corpora, 10)
        self.assertNotIn("notes:secret/keys.md", refs)
        self.assertNotIn("notes:image.txt", refs)
        self.assertIn("logs:day.jsonl", refs)

    def test_cmd_retriever_gets_question_on_stdin(self):
        refs = memeval.cmd_retrieve("sed 's/^/notes:/'", "garden.md", 5)
        self.assertEqual(refs, ["notes:garden.md"])

    def test_run_scores_hits_and_skips_abstention(self):
        self.save(self.rec(),
                  self.rec(id="q2", question="Who fixed the bicycle chain?", gold=["notes:misc.md"]),
                  self.rec(id="q3", category="abstention", question="Which pond did he dig?",
                           answer="not found", keys=[], gold=[]))
        rows = memeval.run(memeval.load(self.q), self.corpora, None, 5)
        by = {r["id"]: r for r in rows}
        self.assertEqual(by["q1"]["rank"], 1)
        self.assertTrue(by["q1"]["hit"])
        self.assertIsNone(by["q3"]["hit"])


class Check(Base):
    def errors(self, *recs):
        self.save(*recs)
        return memeval.check(self.q, self.corpora, freeze=False)

    def test_valid_record_passes(self):
        self.assertEqual(self.errors(self.rec()), [])

    def test_bad_records_are_caught(self):
        cases = {
            "missing gold file": self.rec(gold=["notes:nope.md"]),
            "excluded gold": self.rec(gold=["notes:secret/keys.md"]),
            "key absent from gold": self.rec(keys=["oak"]),
            "key in question": self.rec(keys=["trellis"]),
            "abstention with gold": self.rec(category="abstention", keys=[]),
            "unknown category": self.rec(category="vibes"),
            "missing field": {k: v for k, v in self.rec().items() if k != "as_of"},
        }
        for name, r in cases.items():
            self.assertTrue(self.errors(r), name)
        self.assertTrue(self.errors(self.rec(), self.rec()), "duplicate id")

    def test_key_alternatives(self):
        self.assertEqual(self.errors(self.rec(keys=["oak|cedar"])), [])

    def test_freeze_detects_edit_to_frozen_only(self):
        self.save(self.rec(), self.rec(id="h1", split="heldout"))
        self.assertEqual(memeval.check(self.q, self.corpora, freeze=True), [])
        self.save(self.rec(), self.rec(id="h1", split="heldout", answer="Cedar, in May."))
        self.assertEqual(memeval.check(self.q, self.corpora, freeze=False), [])
        self.save(self.rec(answer="Pine."), self.rec(id="h1", split="heldout"))
        self.assertTrue(memeval.check(self.q, self.corpora, freeze=False))


class Answers(Base):
    def test_keys_and_abstention(self):
        qs = [self.rec(keys=["cedar", "May|spring"]),
              self.rec(id="q2", category="abstention", answer="not found", keys=[], gold=[])]
        got = memeval.score_answers(qs, {"q1": "Cedar posts, in spring.", "q2": "Not found in the notes."})
        self.assertEqual(got, {"q1": True, "q2": True})
        got = memeval.score_answers(qs, {"q1": "Cedar.", "q2": "He dug the north pond."})
        self.assertEqual(got, {"q1": False, "q2": False})


class Cli(Base):
    def test_check_exit_code(self):
        self.save(self.rec(keys=["oak"]))
        p = subprocess.run([sys.executable, os.path.join(HERE, "memeval.py"), "check", self.q,
                            self.corpora_path], capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
