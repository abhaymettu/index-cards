"""Fixture tests for the index-card indexer. Run: /usr/bin/python3 -m unittest test_indexer -v"""
import ast
import fcntl
import getpass
import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout

import indexer

FILES = {
    "People/Ann Lee.md": "---\nname: Ann Lee\ncontext: climbing gym\n---\n\n## Source facts\n\n> met at the gym\n",
    "01-Projects/Alpha-Engine.md": "---\ntitle: Alpha-Engine\ncreated: 2026-09-01\n---\n\nAlpha Engine builds widgets for Ann Lee.\n",
    "00-Inbox/Daily/2026-10-01.md": (
        "# Inbox\n\n**09:15 Alpha engine kickoff** `#capture`\n\nTalked to Ann about scope.\n\n"
        "**10:00 Unrelated** `#capture`\n\nNothing here.\n\n"
        "**11:00 Reading list** `#capture`\n\nOkafor Y, Cummins N. A paper.\n"),
    "03-Resources/Notes.md": "Okafor et al. 2023 found things. Also Okafor wants the draft.\n",
    "03-Resources/Credentials/key.md": "Alpha Engine token below\n",
    "03-Resources/Leak.md": "Alpha Engine key sk-abcdefghijklmnopqrstuvwxyz0123456789ABCD\n",
    "index-cards/_registry.md": "## person\n- Okafor: Okafor\n\n## harness\n- widgetd: widgetd\n",
}
AUDIT = {"lane-2026-10-02.md": "# Lane report\n\nwidgetd restarted; Alpha Engine untouched.\n"}
LAYOUT = {"person_dirs": ["People"], "project_dirs": ["01-Projects"], "block_dirs": ["00-Inbox/Daily/"],
          "skip_dirs": ["03-Resources/Credentials"]}


def rec(kind, text, ts, src, **extra):
    return dict({"kind": kind, "text": text, "ts": ts, "src": src}, **extra)


# digest.py output: s1 names Alpha Engine in a prompt and again in its subagent; s2 only in a reply.
DIGESTS = {
    "p/s1.jsonl": [rec("session", "Widget work", "2026-10-02T14:00:00Z", "session:p/s1.jsonl",
                       title="Widget work", cwd="/tmp/elsewhere"),
                   rec("prompt", "Fix the Alpha Engine build", "2026-10-02T14:05:00Z", "session:p/s1.jsonl#L3"),
                   rec("reply", "Asked Ann Lee too.", "2026-10-02T14:06:00Z", "session:p/s1.jsonl#L4")],
    "p/s1/subagents/agent-a.jsonl": [
        rec("session", "", "2026-10-02T14:07:00Z", "session:p/s1/subagents/agent-a.jsonl"),
        rec("prompt", "Review Alpha Engine tests", "2026-10-02T14:07:00Z", "session:p/s1/subagents/agent-a.jsonl#L1")],
    "p/s2.jsonl": [rec("session", "Other", "2026-10-02T15:00:00Z", "session:p/s2.jsonl", title="Other", cwd="/tmp"),
                   rec("prompt", "hello", "2026-10-02T15:00:00Z", "session:p/s2.jsonl#L2"),
                   rec("reply", "Alpha Engine is fine.", "2026-10-02T15:01:00Z", "session:p/s2.jsonl#L3")],
}


def read(p):
    with open(p) as f:
        return f.read()


def write(p, text):
    with open(p, "w") as f:
        f.write(text)


def digest(root):
    h = hashlib.sha1()
    for d, _, fs in sorted(os.walk(root)):
        for f in sorted(fs):
            p = os.path.join(d, f)
            if "/index-cards/" not in p or p.endswith("_registry.md"):
                with open(p, "rb") as f:
                    h.update(p.encode() + f.read())
    return h.hexdigest()


class IndexerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.home = os.environ["HOME"]
        os.environ["HOME"] = indexer.HOME = self.tmp       # links render as ~/audit/..., ~/digests/...
        self.vault, self.audit = os.path.join(self.tmp, "vault"), os.path.join(self.tmp, "audit")
        self.digests = os.path.join(self.tmp, "digests")
        sessions = {rel: "".join(json.dumps(r) + "\n" for r in recs) for rel, recs in DIGESTS.items()}
        for files, root in ((FILES, self.vault), (AUDIT, self.audit), (sessions, self.digests)):
            for rel, text in files.items():
                p = os.path.join(root, rel)
                os.makedirs(os.path.dirname(p), exist_ok=True)
                write(p, text)
        indexer.configure(dict(LAYOUT, vault=self.vault, audit=self.audit, session_digests=self.digests,
                               lock=os.path.join(self.tmp, "x.lock")))

    def tearDown(self):
        os.environ["HOME"] = indexer.HOME = self.home
        shutil.rmtree(self.tmp)

    def sweep(self):
        with redirect_stdout(io.StringIO()):
            return indexer.run()

    def card(self, kind, slug):
        return read(os.path.join(self.vault, "index-cards", kind, slug + ".md"))

    def test_extra_files_are_sources(self):
        os.makedirs(os.path.join(self.tmp, "lane"))
        write(os.path.join(self.tmp, "lane", "RUNLOG.md"), "# Lane\n\nwidgetd restarted; Alpha Engine untouched.\n")
        indexer.configure(dict(LAYOUT, vault=self.vault, audit=self.audit, session_digests=self.digests,
                               lock=os.path.join(self.tmp, "x.lock"), extra_files=["~/*/RUNLOG.md"]))
        self.sweep()
        self.assertIn("`~/lane/RUNLOG.md`", self.card("project", "alpha-engine"))

    def test_cards_link_every_source(self):
        self.sweep()
        ann = self.card("person", "ann-lee")
        self.assertIn("[[01-Projects/Alpha-Engine|Alpha-Engine]]", ann)
        self.assertIn("2026-10-01 09:15", ann)          # first-name alias, capture time
        self.assertIn("climbing gym", ann)                # seeded one line
        alpha = self.card("project", "alpha-engine")
        self.assertIn("`~/audit/lane-2026-10-02.md`", alpha)
        self.assertIn("(defining note)", alpha)
        self.assertIn("`~/audit/lane-2026-10-02.md`", self.card("harness", "widgetd"))
        self.assertIn("[[index-cards/project/alpha-engine|Alpha-Engine]]",
                      read(indexer.CATALOG))

    def test_second_sweep_writes_nothing_and_sources_untouched(self):
        before = digest(self.vault)
        self.sweep()
        self.assertEqual(self.sweep(), 0)
        self.assertEqual(digest(self.vault), before)

    def test_summary_preserved_and_timeline_updated(self):
        self.sweep()
        p = os.path.join(self.vault, "index-cards/project/alpha-engine.md")
        text = read(p).replace("- Open: \n", "- Open: ship v2 by Friday\n")
        write(p, text)
        with open(os.path.join(self.vault, "00-Inbox/Daily/2026-10-01.md"), "a") as f:
            f.write("\n**12:00 Alpha engine shipped** `#capture`\n\nDone.\n")
        self.assertGreater(self.sweep(), 0)
        after = read(p)
        self.assertIn("- Open: ship v2 by Friday", after)
        self.assertIn("Alpha engine shipped", after)
        self.assertEqual(after.count("Alpha engine kickoff"), 1)

    def test_bullet_metadata_parsed_preserved_and_reported(self):
        self.sweep()
        p = os.path.join(self.vault, "index-cards/project/alpha-engine.md")
        sourced = "- Decision: ship v2 on Friday [source: k:0123456789, 01-Projects/Alpha-Engine.md; added: 2026-10-05]"
        bare = "- Open: find a tester"
        write(p, read(p).replace("- Open: \n", sourced + "\n" + bare + "\n"))
        with open(os.path.join(self.vault, "00-Inbox/Daily/2026-10-01.md"), "a") as f:
            f.write("\n**12:00 Alpha engine shipped** `#capture`\n\nDone.\n")
        out = io.StringIO()
        with redirect_stdout(out):
            indexer.run()
        after = read(p)
        self.assertIn(sourced + "\n" + bare + "\n", after)          # byte for byte through a Timeline rewrite
        self.assertIn("Alpha engine shipped", after)
        self.assertEqual(indexer.unsourced(after), [bare])
        self.assertIn(" unsourced=1 ", out.getvalue())
        meta = indexer.bullet_meta(sourced)
        self.assertEqual((meta["source"], meta["added"]), (["k:0123456789", "01-Projects/Alpha-Engine.md"], "2026-10-05"))
        self.assertEqual(indexer.bullet_meta("- State: done (since 2026-09-01; k:0123456789, k:abcdefabcd)")["source"],
                         ["k:0123456789", "k:abcdefabcd"])
        self.assertIsNone(indexer.bullet_meta("- Fact: no date [source: k:0123456789]"))
        self.assertRegex(self.card("person", "ann-lee"),           # a new card's seeded one-liner is sourced
                         r"- One line: climbing gym \[source: People/Ann Lee\.md; added: \d{4}-\d{2}-\d{2}\]\n")
        out = io.StringIO()
        with redirect_stdout(out):
            indexer.sys.argv = ["indexer.py", "--unsourced"]
            indexer.main()
        self.assertEqual(out.getvalue(), "project/alpha-engine.md: " + bare + "\n")

    def test_gone_source_kept_and_marked(self):
        self.sweep()
        os.remove(os.path.join(self.audit, "lane-2026-10-02.md"))
        self.sweep()
        self.assertIn("lane-2026-10-02.md` · Lane report: widgetd restarted; Alpha Engine untouched. (source gone)",
                      self.card("harness", "widgetd"))

    def test_secrets_and_citations(self):
        self.sweep()
        alpha = self.card("project", "alpha-engine")
        self.assertNotIn("Credentials", alpha)
        self.assertNotIn("sk-abc", alpha)
        self.assertIn("[[03-Resources/Leak|Leak]] · Leak <!--k:", alpha)   # entry kept, excerpt dropped
        okafor = self.card("person", "okafor")
        self.assertIn("Also Okafor wants the draft", okafor)
        self.assertNotIn("reading list", okafor)            # "Okafor Y, Cummins N." is a citation
        self.assertNotIn("—", okafor)

    def test_sessions_on_project_cards(self):
        self.sweep()
        alpha = self.card("project", "alpha-engine")
        when = indexer.local_time("2026-10-02T14:05:00Z")
        self.assertIn("- " + when + " · `~/digests/p/s1.jsonl` · Widget work: "
                      "Fix the Alpha Engine build · from `session:p/s1.jsonl#L3` <!--k:", alpha)
        self.assertEqual(alpha.count("session:p/s1"), 1)    # the subagent folds into its parent
        self.assertNotIn("session:p/s2", alpha)             # assistant text is not matched
        self.assertNotIn("session:", self.card("person", "ann-lee"))   # project cards only
        self.assertEqual(self.sweep(), 0)

    def test_session_digest_gone_kept_and_marked(self):
        self.sweep()
        os.remove(os.path.join(self.digests, "p/s1.jsonl"))
        shutil.rmtree(os.path.join(self.digests, "p/s1"))
        self.sweep()
        self.assertIn("from `session:p/s1.jsonl#L3` (source gone) <!--k:", self.card("project", "alpha-engine"))

    def test_core_has_no_personal_paths(self):
        """Open-source prep: user names, home paths and vault folder names live in the instance
        config ($INDEX_CONFIG), never in the core."""
        tree = ast.parse(read(indexer.__file__))
        consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        cfg = indexer.load_config(indexer.CONFIG)
        values = [v for x in cfg.values() for v in (x if isinstance(x, list) else [x]) if isinstance(v, str)]
        banned = [getpass.getuser(), "/Users/", "iCloud~"] + [v for v in values if len(v) >= 4]
        for c in consts:
            for b in banned:
                self.assertIsNone(re.search(r"(?<![\w.-])" + re.escape(b) + r"(?![\w.-])", c), (b, c))
            self.assertIsNone(re.search(r"(^|/)\d\d-[A-Z]", c), c)    # numbered vault folders

    def poll(self):
        out = io.StringIO()
        with redirect_stdout(out):
            indexer.sys.argv = ["indexer.py", "--if-changed"]
            indexer.main()
        return "entities=" in out.getvalue()

    def test_poll_ignores_own_writes_and_catches_appends(self):
        self.assertTrue(self.poll())                       # first poll sweeps
        self.assertFalse(self.poll())                      # its own card writes do not re-trigger
        daily = os.path.join(self.vault, "00-Inbox/Daily/2026-10-01.md")
        os.utime(daily, (os.path.getmtime(daily) + 5,) * 2)
        with open(daily, "a") as f:
            f.write("\n**13:00 widgetd note** `#capture`\n")
        self.assertTrue(self.poll())
        self.assertIn("widgetd note", self.card("harness", "widgetd"))

    def test_unreadable_folder_aborts_instead_of_marking_gone(self):
        self.sweep()
        locked = os.path.join(self.vault, "03-Resources")
        os.chmod(locked, 0)
        try:
            with self.assertRaises(PermissionError):
                self.sweep()
        finally:
            os.chmod(locked, 0o755)
        self.assertNotIn("source gone", self.card("project", "alpha-engine"))

    def test_lock_skips_concurrent_run(self):
        with open(indexer.LOCK, "w") as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            out = io.StringIO()
            with redirect_stdout(out):
                indexer.sys.argv = ["indexer.py"]
                indexer.main()
            self.assertIn("skipping", out.getvalue())
        self.assertFalse(os.path.exists(indexer.CATALOG))


if __name__ == "__main__":
    unittest.main()
