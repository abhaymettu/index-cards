#!/usr/bin/python3
"""Tests for consolidate.py with a fake model: no network, no claude call."""
import argparse, json, os, subprocess, sys, tempfile, unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import consolidate as C

CARD = """---
type: index-card
kind: project
entity: "Tempo"
entries: 3
---

# Tempo

## Summary

- One line: seeded line
- Summary as of: 2026-10-01 (seeded by the indexer; rewrite freely)

## Timeline

Newest first.

<!-- index:start -->
- 2026-10-03 13:49 · [[01-Projects/tempo/plan|plan]] · Tempo switched the store to sqlite <!--k:aaaaaaaaaa-->
- 2026-09-20 · `~/audit/tempo-audit.md` · Tempo audit: store is postgres for now <!--k:bbbbbbbbbb-->
- 2026-09-01 · [[00-Inbox/Daily/2026-09-01|2026-09-01]] · started Tempo, a time tracker <!--k:cccccccccc-->
<!-- index:end -->
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.cards = os.path.join(self.d, "index-cards")
        os.makedirs(os.path.join(self.cards, "project"))
        self.path = os.path.join(self.cards, "project", "tempo.md")
        self.write(CARD)
        self.calls = []
        self.reply = {"facts": []}

    def write(self, text):
        with open(self.path, "w") as f:
            f.write(text)

    def fake(self, rel, text, ents, facts, model, base):
        self.calls.append((rel, facts))
        return self.reply, 0.0

    def run_pass(self, **kw):
        a = argparse.Namespace(cards=self.cards, vault=self.d, state=os.path.join(self.d, "state.json"),
                               lock=None, jobs=2, model="x", only=None, dry_run=False, commit=False)
        vars(a).update(kw)
        return C.run(a, model_call=self.fake)

    def card(self):
        return C.read(self.path)


class TestPass(Base):
    def test_provenance_rejects(self):
        self.reply = {"facts": [
            {"kind": "Fact", "text": "Tempo is a time tracker", "cite": []},                 # no_cite
            {"kind": "Fact", "text": "Tempo is a time tracker", "cite": [7]},                # bad_cite
            {"kind": "Fact", "text": "Quantum gardening wins", "cite": [2]},                 # unsupported
            {"kind": "Overview", "text": "Tempo is a time tracker", "cite": [2]}]}           # ok
        t = self.run_pass()
        self.assertEqual((t["no_cite"], t["bad_cite"], t["unsupported"], t["accepted"]), (1, 1, 1, 1))
        self.assertIn("- Overview: Tempo is a time tracker (since 2026-09-01; k:cccccccccc)", self.card())
        self.assertNotIn("Quantum", self.card())

    def test_only_summary_changes_and_old_summary_archived(self):
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0]}]}
        self.run_pass()
        new, old = self.card(), CARD
        self.assertEqual(new[:new.index("## Summary")], old[:old.index("## Summary")])
        self.assertEqual(new[new.index("## Timeline"):], old[old.index("## Timeline"):])
        self.assertIn(C.ARCHIVED, new)
        self.assertIn("- One line: seeded line", new)          # never deleted, archived verbatim

    def test_supersession_follows_dates(self):
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is postgres", "cite": [1]}]}
        self.run_pass()
        self.write(self.card().replace("<!-- index:end -->",
                   "- 2026-08-01 · `~/x.md` · Tempo store note <!--k:dddddddddd-->\n<!-- index:end -->"))
        # newer evidence replaces: old fact moves to Superseded with the new date
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0], "replaces": ["F0"]}]}
        t = self.run_pass()
        self.assertEqual(t["superseded"], 1)
        c = self.card()
        active, sup = c.split(C.SUPERSEDED)[0], c.split(C.SUPERSEDED)[1].split(C.ARCHIVED)[0]
        self.assertIn("- State: Tempo store is sqlite (since 2026-10-03; k:aaaaaaaaaa)", active)
        self.assertIn("Tempo store is postgres (since 2026-09-20; k:bbbbbbbbbb) · superseded 2026-10-03 by "
                      "Tempo store is sqlite", sup)

    def test_superseded_points_at_newest_key(self):
        # IDs run newest first, so the last cited key is the oldest; the pointer names the newest
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is postgres", "cite": [2]}]}
        self.run_pass()
        self.write(self.card().replace("<!-- index:end -->",
                   "- 2026-08-01 · `~/x.md` · Tempo store note <!--k:dddddddddd-->\n<!-- index:end -->"))
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0, 1], "replaces": ["F0"]}]}
        self.run_pass()
        self.assertIn("superseded 2026-10-03 by Tempo store is sqlite (k:aaaaaaaaaa)", self.card())

    def test_older_update_does_not_win(self):
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0]}]}
        self.run_pass()
        self.write(self.card().replace("<!-- index:end -->",
                   "- 2026-08-01 · `~/x.md` · Tempo store note <!--k:dddddddddd-->\n<!-- index:end -->"))
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is postgres", "cite": [1], "replaces": ["F0"]}]}
        self.run_pass()
        active = self.card().split(C.SUPERSEDED)[0]
        self.assertIn("Tempo store is sqlite", active)
        self.assertNotIn("postgres", active)

    def test_multi_replace_is_all_or_nothing(self):
        self.reply = {"facts": [{"kind": "State", "text": "Tempo started as a time tracker", "cite": [2]},
                                {"kind": "State", "text": "Tempo store is sqlite", "cite": [0]}]}
        self.run_pass()
        self.write(self.card().replace("<!-- index:end -->",
                   "- 2026-08-01 · `~/x.md` · Tempo store note <!--k:dddddddddd-->\n<!-- index:end -->"))
        # beats F0 (2026-09-01) but loses to F1 (2026-10-03): nothing may leave the active list
        self.reply = {"facts": [{"kind": "State", "text": "Tempo audit says store is postgres", "cite": [1],
                                 "replaces": ["F0", "F1"]}]}
        t = self.run_pass()
        active = self.card().split(C.SUPERSEDED)[0]
        self.assertEqual(t["superseded"], 0)
        self.assertIn("Tempo started as a time tracker", active)
        self.assertIn("Tempo store is sqlite", active)
        self.assertNotIn("postgres", active)

    def test_only_limits_the_pass(self):
        with open(os.path.join(self.cards, "project", "other.md"), "w") as f:
            f.write(CARD)
        self.run_pass(only="project/tempo.md")
        self.assertEqual([c[0] for c in self.calls], ["project/tempo.md"])

    def test_model_cannot_delete(self):
        self.reply = {"facts": [{"kind": "Open", "text": "Tempo needs a store decision", "cite": [1]}]}
        self.run_pass()
        self.write(self.card().replace("<!-- index:end -->",
                   "- 2026-08-01 · `~/x.md` · Tempo store note <!--k:dddddddddd-->\n<!-- index:end -->"))
        self.reply = {"facts": []}
        self.run_pass()
        self.assertIn("- Open: Tempo needs a store decision", self.card())

    def test_empty_reply_is_byte_identical(self):
        ents = C.entries(CARD, self.d)
        once, _ = C.consolidate(CARD, ents, [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0]}], "d")
        self.assertEqual(C.consolidate(once, ents, [], "d")[0], once)

    def test_unchanged_timeline_is_skipped(self):
        self.run_pass()
        self.run_pass()
        self.assertEqual(len(self.calls), 1)
        self.write(self.card().replace("<!-- index:end -->",
                   "- 2026-08-01 · `~/x.md` · Tempo note <!--k:dddddddddd-->\n<!-- index:end -->"))
        self.run_pass()
        self.assertEqual(len(self.calls), 2)

    def test_dry_run_writes_nothing(self):
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0]}]}
        self.run_pass(dry_run=True)
        self.assertEqual(self.card(), CARD)
        self.assertFalse(os.path.exists(os.path.join(self.d, "state.json")))

    def test_fact_with_gone_keys_is_retired_not_deleted(self):
        self.reply = {"facts": [{"kind": "Fact", "text": "Tempo audit says postgres", "cite": [1]}]}
        self.run_pass()
        self.write(self.card().replace(" <!--k:bbbbbbbbbb-->", " <!--k:eeeeeeeeee-->"))
        self.reply = {"facts": []}
        t = self.run_pass()
        self.assertEqual(t["orphaned"], 1)
        self.assertIn("Tempo audit says postgres (since 2026-09-20; k:bbbbbbbbbb) · retired", self.card())

    def test_hand_bullet_without_key_is_archived(self):
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0]}]}
        self.run_pass()
        self.write(self.card().replace("- State: Tempo", "- my own note\n- State: Tempo").replace(
            "<!-- index:end -->", "- 2026-08-01 · `~/x.md` · Tempo n <!--k:dddddddddd-->\n<!-- index:end -->"))
        self.reply = {"facts": []}
        self.run_pass()
        active, arch = self.card().split(C.ARCHIVED)
        self.assertNotIn("my own note", active)
        self.assertIn("- my own note", arch)

    def test_commit_only_written_cards(self):
        subprocess.run(["git", "init", "-q", self.d], check=True)
        other = os.path.join(self.d, "other.md")
        open(other, "w").write("untracked\n")
        subprocess.run(["git", "-C", self.d, "add", "index-cards"], check=True)
        subprocess.run(["git", "-C", self.d, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"],
                       check=True)
        self.reply = {"facts": [{"kind": "State", "text": "Tempo store is sqlite", "cite": [0]}]}
        with mock.patch.dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
                             GIT_COMMITTER_EMAIL="t@t"):
            self.run_pass(commit=True)
        files = subprocess.run(["git", "-C", self.d, "show", "--name-only", "--format=%s"], capture_output=True,
                               text=True).stdout.split()
        self.assertIn("index-cards/project/tempo.md", files)
        self.assertNotIn("other.md", files)


class TestLint(Base):
    def test_lint_reports_and_edits_nothing(self):
        self.reply = {"facts": [{"kind": "Open", "text": "Tempo store decision pending", "cite": [1]}]}
        self.run_pass()
        self.write(self.card().replace("- Open: Tempo", "- loose hand line\n- Open: Tempo"))
        before = self.card()
        out = os.path.join(self.d, "lint.md")
        seen = []

        def fake_call(prompt, schema, cwd, model):
            seen.append(prompt)
            return {"pairs": [{"a": "project/tempo.md#F0", "b": "nope#F1", "why": "x"}]}, 0
        a = argparse.Namespace(cards=self.cards, state=os.path.join(self.d, "state.json"), out=out,
                               stale_days=5, llm=True, model="x")
        C.lint(a, model_call=fake_call)
        rep = C.read(out)
        self.assertEqual(self.card(), before)
        self.assertIn("## Uncited active bullets (1)", rep)
        self.assertIn("## Open items with no citation newer than", rep)
        self.assertIn("Tempo store decision pending", rep.split("## Orphans")[0].split("Open items")[1])
        self.assertIn("## Pending a consolidation pass (0)", rep)          # a Summary edit is not a Timeline change
        self.assertIn("1 dropped: unknown IDs", rep)
        self.assertIn("project/tempo.md#F0 Open: Tempo store decision pending", seen[0])

    def test_no_personal_paths(self):
        src = C.read(C.__file__)
        for s in ("/Users/", "iCloud~", "01-Projects"):
            self.assertNotIn(s, src)


if __name__ == "__main__":
    unittest.main()
