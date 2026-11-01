#!/usr/bin/env python3
"""Fixture tests for digest. Run: /usr/bin/python3 digest/test_digest.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import digest  # noqa: E402

KEY = "sk-ant-api03-" + "Ab1" * 12


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(text)


def rec(type_, content, ts="2026-09-01T10:00:00Z", **kw):
    return json.dumps(dict({"type": type_, "timestamp": ts, "sessionId": "s1", "cwd": "/w", "gitBranch": "main",
                            "message": {"role": type_, "content": content}}, **kw))


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f.read().splitlines()]


class Digest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.src = os.path.join(self.tmp, "src")
        self.out = os.path.join(self.tmp, "out")
        session = [
            json.dumps({"type": "ai-title", "aiTitle": "Fix the trellis page", "sessionId": "s1"}),
            rec("user", "Why is the trellis\u2028page blank?<system-reminder>hook noise</system-reminder>"),
            rec("user", "Base directory for this skill", isMeta=True),
            rec("assistant", [{"type": "text", "text": "Checking the page. " + "narration " * 200}]),
            rec("assistant", [{"type": "thinking", "thinking": "private deliberation"},
                              {"type": "text", "text": "The cedar fade-in never fires. Key " + KEY},
                              {"type": "tool_use", "name": "Edit", "input": {"file_path": "/w/site/rig.js"}},
                              {"type": "tool_use", "name": "Bash",
                               "input": {"command": "curl https://example.org/a", "description": "Fetch page"}}]),
            rec("user", [{"type": "tool_result", "content": "tomato " * 5000}]),
            rec("user", "keep this <private>my bank pin</private> part", ts="2026-09-01T11:00:00Z"),
            "not json",
        ]
        write(os.path.join(self.src, "logs/proj/s1.jsonl"), "\n".join(session) + "\n")
        write(os.path.join(self.src, "logs/proj/quiet.jsonl"),
              rec("user", "secret plans. DO NOT INDEX THIS CHAT") + "\n")
        write(os.path.join(self.src, "notes/garden.md"),
              "---\ncreated: 2026-08-02\n---\n# Garden\nIntro line.\n## Trellis\nRebuilt on 2026-08-20 with cedar.\n"
              "```\n# not a heading\n```\n## Beds\nRaised beds.\n")
        write(os.path.join(self.src, "notes/secret/keys.md"), "password stuff\n")
        self.corpora = {
            "logs": {"root": os.path.join(self.src, "logs"), "include": ["*.jsonl"]},
            "notes": {"root": os.path.join(self.src, "notes"), "include": ["*.md"], "exclude": ["secret/**"]},
        }

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_session(self):
        self.assertEqual(digest.build(self.corpora, self.out), {"logs": 2, "notes": 1})
        recs = load(os.path.join(self.out, "logs/proj/s1.jsonl"))
        head = recs[0]
        self.assertEqual((head["kind"], head["title"], head["cwd"], head["start"], head["end"]),
                         ("session", "Fix the trellis page", "/w", "2026-09-01T10:00:00Z", "2026-09-01T11:00:00Z"))
        kinds = [(r["kind"], r["text"]) for r in recs[1:]]
        self.assertIn(("prompt", "Why is the trellis\u2028page blank?"), kinds)
        self.assertIn(("file", "/w/site/rig.js"), kinds)
        self.assertIn(("cmd", "Fetch page"), kinds)
        self.assertIn(("url", "https://example.org/a"), kinds)
        self.assertIn(("prompt", "keep this  part"), kinds)
        body = json.dumps(recs)
        for gone in ("hook noise", "Base directory", "private deliberation", "tomato", "bank pin", KEY[:20]):
            self.assertNotIn(gone, body)
        self.assertIn("[redacted]", body)
        step = next(r for r in recs if r["kind"] == "step")
        self.assertEqual(step["src"], "logs:proj/s1.jsonl#L4")
        self.assertTrue(step["text"].startswith("Checking the page."))
        final = next(r for r in recs if r["kind"] == "reply")
        self.assertTrue(final["text"].startswith("The cedar fade-in never fires"))
        self.assertEqual([len(x) <= digest.CAP for x in digest.pieces("a\n" * 1500)], [True, True])
        quiet = load(os.path.join(self.out, "logs/proj/quiet.jsonl"))
        self.assertEqual(len(quiet), 1)
        self.assertNotIn("secret plans", json.dumps(quiet))

    def test_budget_overflow(self):
        turns = []
        for i in range(60):
            turns += [rec("user", "question %d about cedar %s" % (i, "q" * 300)),
                      rec("assistant", [{"type": "text", "text": "step %d %s" % (i, "s" * 300)}]),
                      rec("assistant", [{"type": "text", "text": "answer %d %s" % (i, "a" * 300)}])]
        write(os.path.join(self.src, "logs/proj/long.jsonl"), "\n".join(turns) + "\n")
        digest.build(self.corpora, self.out)
        main = os.path.join(self.out, "logs/proj/long.jsonl")
        over = os.path.join(self.out, "overflow/logs/proj/long.jsonl")
        self.assertLessEqual(os.path.getsize(main), digest.BUDGET)
        kept, spilled = load(main), load(over)
        self.assertEqual(kept[0]["kind"], "session")
        self.assertEqual(len(kept) - 1 + len(spilled), 180)                    # nothing lost
        self.assertLessEqual({r["kind"] for r in kept[1:]}, {"prompt", "reply"})   # steps rank below
        self.assertEqual(sum(r["kind"] == "step" for r in spilled), 60)
        lines = [int(r["src"].split("#L")[1]) for r in kept[1:]]
        self.assertEqual(lines, sorted(lines))                                  # source order kept

    def test_note(self):
        digest.build(self.corpora, self.out)
        self.assertFalse(os.path.exists(os.path.join(self.out, "notes/secret/keys.md")))
        recs = load(os.path.join(self.out, "notes/garden.md"))
        self.assertEqual(recs[0]["ts"], "2026-08-02")
        secs = {r["heading"]: r for r in recs[1:]}
        self.assertEqual(sorted(secs), ["", "Garden", "Garden > Beds", "Garden > Trellis"])
        self.assertEqual(secs[""]["text"], "created: 2026-08-02")                 # frontmatter kept
        self.assertEqual(secs["Garden > Trellis"]["ts"], "2026-08-20")
        self.assertEqual(secs["Garden > Trellis"]["src"], "notes:garden.md#L7-L7")
        self.assertNotIn("not a heading", json.dumps(recs))

    def test_long_section_split_not_cut(self):
        write(os.path.join(self.src, "notes/long.md"), "# Log\n" + "".join("line %d of the log\n" % i for i in range(400)))
        digest.build(self.corpora, self.out)
        secs = load(os.path.join(self.out, "notes/long.md"))[1:]
        self.assertGreater(len(secs), 1)
        self.assertTrue(all(len(r["text"]) <= digest.CAP for r in secs))
        self.assertIn("line 399 of the log", secs[-1]["text"])
        self.assertEqual(secs[-1]["src"].split("-L")[-1], "401")

    def test_scrub_keeps_paths(self):
        p = "/Users/someone/code/memory-upgrade/specs/003-digests/spec.md"
        u = "-Users-someone-proj/b5cc85e3-a26d-4bb2-b64b-e74f6a795fe1.jsonl"
        self.assertEqual(digest.scrub(p + " " + u), p + " " + u)
        self.assertEqual(digest.scrub("tok " + "aB3" * 11), "tok [redacted]")
        self.assertEqual(digest.scrub("sha " + "0123456789abcdef" * 4), "sha [redacted]")

    def test_incremental_and_archive(self):
        digest.build(self.corpora, self.out)
        self.assertEqual(digest.build(self.corpora, self.out), {"logs": 0, "notes": 0})
        note = os.path.join(self.src, "notes/garden.md")
        write(note, "# Garden\nOnly this now.\n")
        os.utime(note, (2e9, 2e9))
        digest.build(self.corpora, self.out)
        archived = os.listdir(os.path.join(self.out, "archive/notes"))
        self.assertEqual(len(archived), 1)
        self.assertTrue(archived[0].startswith("garden.md."))
        os.remove(note)
        digest.build(self.corpora, self.out)
        self.assertTrue(os.path.exists(os.path.join(self.out, "notes/garden.md")))   # outlives its source

    def test_growing_session_not_archived(self):
        digest.build(self.corpora, self.out)
        s = os.path.join(self.src, "logs/proj/s1.jsonl")
        with open(s, "a") as f:
            f.write(rec("user", "one more question", ts="2026-09-01T12:00:00Z") + "\n")
        os.utime(s, (2e9, 2e9))
        digest.build(self.corpora, self.out)
        self.assertFalse(os.path.exists(os.path.join(self.out, "archive")))


if __name__ == "__main__":
    unittest.main()
