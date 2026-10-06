"""Fixture tests for the nightly loop. Run: cd nightly && /usr/bin/python3 -m unittest test_nightly -v
Needs ripgrep on PATH for the gate tests (memeval's retriever)."""
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

import nightly

CARD = """---
type: index-card
kind: project
entity: "Alpha"
aliases: ["Alpha"]
entries: 2
last_seen: 2026-09-20
updated: 2026-09-20 10:00
---

# Alpha

## Summary

- One line: Alpha builds widgets [source: 01-Projects/Alpha.md; added: 2026-09-01]
- Defining notes: [[01-Projects/Alpha|Alpha]]
- Decision: ship v2 on Friday [source: k:aaaaaaaaaa; added: 2026-09-10]
- Decision: ship v2 on Friday [source: k:aaaaaaaaaa; added: 2026-09-10]
- State: the beta has 12 testers [source: k:aaaaaaaaaa; added: 2026-09-12]
- State: the beta has 20 testers [source: k:bbbbbbbbbb; added: 2026-09-20]
- Open: find a tester for the widget build
- Open: find a tester for the widget build soon
- Fact: the launch is set for early October [source: k:aaaaaaaaaa; added: 2026-09-05]
- Fact: the launch is set for early October indeed [source: k:bbbbbbbbbb; added: 2026-09-15]
- Fact: old thing [source: k:cccccccccc; added: 2026-01-01]
- Links: [[Nowhere Note]]
- Summary as of: 2026-09-01 (seeded by the indexer; rewrite freely, the indexer never touches this section)

## Timeline

Newest first. Maintained by the indexer; edits between the markers are overwritten.

<!-- index:start -->
- 2026-09-20 · [[01-Projects/Alpha|Alpha]] · Alpha (defining note) <!--k:bbbbbbbbbb-->
- 2026-09-10 · [[People/Ann Lee|Ann Lee]] · Ann Lee: widgets for Alpha <!--k:aaaaaaaaaa-->
<!-- index:end -->
"""
NOTES = {"People/Ann Lee.md": "---\nname: Ann Lee\ncontext: climbing gym\n---\n\nAnn Lee likes widgets from Alpha.\n",
         "01-Projects/Alpha.md": "---\ntitle: Alpha\n---\n\nAlpha builds widgets for Ann Lee.\n"}
QUESTIONS = [{"id": "q1", "category": "single", "question": "how many beta testers does the widget project have",
              "answer": "20", "keys": ["20"], "gold": ["vault:index-cards/project/alpha.md"], "as_of": "2026-09-20",
              "split": "frozen", "note": ""},
             {"id": "q2", "category": "single", "question": "where did he meet Ann Lee, the climbing gym person",
              "answer": "gym", "keys": ["gym"], "gold": ["vault:People/Ann Lee.md"], "as_of": "2026-09-20",
              "split": "frozen", "note": ""}]


def write(p, text):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(text)


def read(p):
    with open(p) as f:
        return f.read()


class NightlyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.vault = os.path.join(self.tmp, "vault")
        self.cards = os.path.join(self.vault, "index-cards")
        for rel, text in NOTES.items():
            write(os.path.join(self.vault, rel), text)
        write(os.path.join(self.cards, "project", "alpha.md"), CARD)
        self.icfg = os.path.join(self.tmp, "indexer.json")
        write(self.icfg, json.dumps({"vault": self.vault, "lock": os.path.join(self.tmp, "x.lock"),
                                     "person_dirs": ["People"], "project_dirs": ["01-Projects"]}))
        write(os.path.join(self.tmp, "corpora.json"), json.dumps({"vault": {"root": self.vault, "include": ["*.md"]}}))
        write(os.path.join(self.tmp, "q.jsonl"), "".join(json.dumps(q) + "\n" for q in QUESTIONS))
        self.cfg_path = os.path.join(self.tmp, "nightly.json")
        self.cfg = {"indexer_config": self.icfg, "questions": os.path.join(self.tmp, "q.jsonl"),
                    "corpora": os.path.join(self.tmp, "corpora.json"), "out": os.path.join(self.tmp, "out")}
        write(self.cfg_path, json.dumps(self.cfg))
        self.today = date.today().isoformat()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_(self, **kw):
        out = io.StringIO()
        with redirect_stdout(out):
            return nightly.run(self.cfg, self.cfg_path, **kw), out.getvalue()

    def test_passes_propose_the_expected_change_set(self):
        findings, proposed, n = nightly.analyse(self.cards, self.vault, 90, self.today)
        self.assertEqual((n, list(proposed)), (1, ["project/alpha.md"]))
        old, new = proposed["project/alpha.md"]
        self.assertEqual({p: len(v) for p, v in findings.items()},
                         {"unsourced": 2, "exact_dup": 1, "near_dup": 2, "contradiction": 1, "stale": 1, "broken_link": 1})
        self.assertEqual(new.count("- Decision: ship v2 on Friday"), 1)
        self.assertNotIn("- Open: find a tester for the widget build\n", new)
        self.assertIn("- Open: find a tester for the widget build soon\n", new)
        self.assertIn("- Fact: the launch is set for early October indeed [source: k:bbbbbbbbbb, k:aaaaaaaaaa; "
                      "added: 2026-09-05]\n", new)
        self.assertIn("\n### Superseded\n\n- State: the beta has 12 testers [source: k:aaaaaaaaaa; added: 2026-09-12]"
                      " · superseded 2026-09-20 by the beta has 20 testers\n- Fact: old thing [source: k:cccccccccc; "
                      "added: 2026-01-01] · retired %s: source gone (k:cccccccccc)\n\n## Timeline" % self.today, new)
        self.assertIn("project/alpha.md: [[Nowhere Note]]", findings["broken_link"])
        self.assertEqual(nightly.indexer.owned(new).count("<!--k:"), 0)
        self.assertNotIn("—", new)
        # Idempotent: the proposed card proposes nothing more.
        write(os.path.join(self.cards, "project", "alpha.md"), new)
        _, again, _ = nightly.analyse(self.cards, self.vault, 90, self.today)
        self.assertEqual(again, {})

    def test_propose_writes_patch_and_report_only(self):
        entry, out = self.run_()
        self.assertEqual((entry["decision"], entry["proposed_cards"]), ("proposed", 1))
        self.assertEqual(read(os.path.join(self.cards, "project", "alpha.md")), CARD)   # nothing edited
        copy = os.path.join(self.tmp, "copy")
        shutil.copytree(self.cards, copy)
        subprocess.run(["patch", "-p1", "-s", "-d", copy, "-i", entry["patch"]], check=True)
        _, proposed, _ = nightly.analyse(self.cards, self.vault, 90, self.today)
        self.assertEqual(read(os.path.join(copy, "project", "alpha.md")), proposed["project/alpha.md"][1])
        report = read(entry["report"])
        self.assertIn("| exact_dup | 1 |", report)
        self.assertIn("## Schedule (not installed)", report)
        self.assertIn("NIGHTLY_CONFIG=" + self.cfg_path, report)
        self.assertIn("not run (no --llm)", out)
        self.assertEqual(len(read(os.path.join(self.tmp, "out", "ledger.jsonl")).splitlines()), 1)

    def test_gate_rejects_a_lower_score_and_writes_nothing(self):
        real = nightly.score
        nightly.score = lambda cfg, d, qs: {"n": 2, "hits": 2 if d == self.cards else 1, "mrr": 1.0}
        try:
            entry, _ = self.run_(apply=True)
        finally:
            nightly.score = real
        self.assertEqual(entry["decision"], "rejected: score")
        self.assertEqual(read(os.path.join(self.cards, "project", "alpha.md")), CARD)

    def test_gate_scores_sweeps_and_applies_under_the_lock(self):
        entry, _ = self.run_(apply=True)
        self.assertEqual(entry["decision"], "applied", entry)
        self.assertEqual(entry["score_before"], entry["score_after"])
        self.assertEqual(entry["score_before"]["hits"], 2)       # gold vault:index-cards/... maps onto the cards corpus
        self.assertEqual(entry["sweep"]["lost"], [])
        self.assertIn("entities=", entry["sweep"]["line"])
        self.assertEqual(entry["written"], ["project/alpha.md"])
        self.assertIn("### Superseded", read(os.path.join(self.cards, "project", "alpha.md")))
        self.assertFalse(os.path.exists(os.path.join(self.cards, "person")))    # the sweep ran in scratch, not here
        lines = read(os.path.join(self.tmp, "out", "ledger.jsonl")).splitlines()
        self.assertEqual(json.loads(lines[-1])["decision"], "applied")
        entry2, _ = self.run_(apply=True)
        self.assertEqual(entry2["decision"], "nothing to apply")


if __name__ == "__main__":
    unittest.main()
