#!/usr/bin/env python3
"""Build the Claude Code style memory baseline: the model reads the vault one week at a time, in
date order, and rewrites a MEMORY.md capped at BUDGET tokens after each week, the way Claude Code's
auto memory keeps a file it loads at the start of every session.

  memory_build.py [--budget 4000] [--model sonnet]

Writes bench/cache/memory-<budget>.md and a log of every intermediate version.
"""
import argparse
import collections
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from llm import ask  # noqa: E402
from systems import ROOT, load_chunks  # noqa: E402

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
SYSTEM = """You are Claude Code's auto memory for one user. You keep MEMORY.md, a file loaded into your context at the
start of every future session so you can answer the user's questions about their own notes, people and projects
without rereading the notes. MEMORY.md is capped at {budget} tokens (about {chars} characters); anything past the cap
is cut off and lost. Save durable, specific facts (names, roles, employers, cities, how and when the user met people,
project owners, languages, hosts, deadlines, statuses, collaborators, notable personal details) with dates where they
help. When a note changes or corrects a fact you saved, edit that entry in place so only the current value remains.
Compress older or less useful material to stay under the cap. Record only what the notes say. Output the complete new MEMORY.md and nothing else."""


def scrub(text):
    """The CLI puts the account's email address in every session's context, and the model sometimes files
    it as a fact about the user. The vault has no email addresses, so any line with one is dropped."""
    return "\n".join(l for l in text.splitlines() if not EMAIL.search(l))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=4000)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--vault", default=os.path.join(ROOT, "vault"))
    a = ap.parse_args()
    world = json.load(open(os.path.join(ROOT, "data", "world.json")))
    notes = collections.defaultdict(list)
    for c in load_chunks(a.vault):
        notes[c.path].append(c)
    weeks = collections.defaultdict(list)
    for path, cs in notes.items():
        date = cs[0].date if not path.startswith("03-Resources") else world["start"]
        weeks[dt.date.fromisoformat(date).isocalendar()[:2]].append((date, path, "\n".join(c.text for c in cs)))
    memory, log = "", []
    sysmsg = SYSTEM.format(budget=a.budget, chars=a.budget * 4)
    for i, wk in enumerate(sorted(weeks)):
        body = "\n\n".join(f"=== {p} ({d}) ===\n{t}" for d, p, t in sorted(weeks[wk]))
        prompt = (f"Current MEMORY.md ({len(memory)} characters):\n<memory>\n{memory}\n</memory>\n\n"
                  f"Notes written this week:\n<notes>\n{body}\n</notes>\n\nOutput the updated MEMORY.md.")
        r = ask(prompt, system=sysmsg, model=a.model)
        memory = scrub(r["result"].strip())
        u = r["usage"]
        log.append({"week": i, "notes": len(weeks[wk]), "chars": len(memory), "wall_s": round(r["wall_s"], 1),
                    "input_tokens": u["input_tokens"] + u.get("cache_creation_input_tokens", 0)
                    + u.get("cache_read_input_tokens", 0), "output_tokens": u["output_tokens"]})
        print(log[-1], flush=True)
    os.makedirs(os.path.join(ROOT, "cache"), exist_ok=True)
    open(os.path.join(ROOT, "cache", f"memory-{a.budget}.md"), "w").write(memory + "\n")
    json.dump(log, open(os.path.join(ROOT, "cache", f"memory-{a.budget}.log.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
