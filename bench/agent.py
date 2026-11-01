#!/usr/bin/env python3
"""Experiment 2: a real agent loop. Claude Code (`claude -p`) gets Read, Grep and Glob inside a copy
of the vault and answers each question itself, under three setups:

  plain    the vault, nothing else
  memory   the vault, plus the memory file loaded into the system prompt the way Claude Code loads
           MEMORY.md at session start
  cards    the vault with index-cards/ built, plus the one-sentence pointer from the README

  agent.py [--setups plain,memory,cards] [--n 90] [--jobs 6] [--model sonnet]

No context budget here: the agent spends what it decides to. The comparison is accuracy, total
input tokens, turns and wall time. Results append to $BENCH_ROOT/results/agent.jsonl.
"""
import argparse
import concurrent.futures as cf
import json
import os
import random
import shutil
import subprocess
import threading
import time

from llm import CLAUDE
from systems import ROOT

BASE = ("You answer questions about the user's personal notes. The notes are the markdown vault in the current "
        "directory. Today is {today}. Use the tools to look things up; do not guess. If sources disagree, trust the "
        "most recent dated one. Finish with one line: ANSWER: <just the answer, dates as YYYY-MM-DD, or unknown if "
        "the notes do not say>.")
POINTER = ("Index cards: index-cards/ holds one card per person and project (list in index-cards/_catalog.md). "
           "Look for a card on the question's subject first, then read the sources it lists.")


def prepare(setup):
    dst = os.path.join(ROOT, "agent", setup)
    if not os.path.exists(dst):
        shutil.copytree(os.path.join(ROOT, "vault"), dst,
                        ignore=None if setup == "cards" else shutil.ignore_patterns("index-cards"))
    return dst


def run_one(setup, q, today, model):
    system = BASE.format(today=today)
    if setup == "memory":
        system += "\n\nContents of MEMORY.md (your memory from earlier sessions):\n" + \
                  open(os.path.join(ROOT, "cache", "memory-4000.md")).read()
    if setup == "cards":
        system += "\n\n" + POINTER
    cmd = [CLAUDE, "-p", "--model", model, "--output-format", "json", "--tools", "Read,Grep,Glob",
           "--no-session-persistence", "--system-prompt", system, "--strict-mcp-config",
           "--setting-sources", "", "--disable-slash-commands", "--max-turns", "30"]
    for attempt in range(3):
        t0 = time.time()
        r = subprocess.run(cmd, input=q["question"], capture_output=True, text=True, cwd=prepare(setup), timeout=900)
        try:
            out = json.loads(r.stdout)
        except json.JSONDecodeError:
            time.sleep(10)
            continue
        text = out.get("result") or ""
        ans = text.rsplit("ANSWER:", 1)[-1].strip() if "ANSWER:" in text else text.strip()[-300:]
        u = out.get("usage", {})
        return {"setup": setup, "model": model, "id": q["id"], "answer": ans, "turns": out.get("num_turns"),
                "wall_s": round(time.time() - t0, 1),
                "input_tokens": u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                + u.get("cache_read_input_tokens", 0), "output_tokens": u.get("output_tokens", 0),
                "subtype": out.get("subtype")}
    raise RuntimeError(r.stderr[-400:])


def sample(qs, n, seed=11):
    """A stratified sample of the test split, the same for every setup."""
    rng = random.Random(seed)
    test = [q for q in qs if q["split"] == "test"]
    cats = sorted({q["category"] for q in test})
    out = []
    for c in cats:
        pool = [q for q in test if q["category"] == c]
        out += rng.sample(pool, min(len(pool), max(4, round(n * len(pool) / len(test)))))
    return sorted(out, key=lambda q: q["id"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setups", default="plain,memory,cards")
    ap.add_argument("--n", type=int, default=90)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--model", default="sonnet")
    a = ap.parse_args()
    world = json.load(open(os.path.join(ROOT, "data", "world.json")))
    qs = sample([json.loads(l) for l in open(os.path.join(ROOT, "data", "questions.jsonl"))], a.n)
    out = os.path.join(ROOT, "results", "agent.jsonl")
    done = set()
    if os.path.exists(out):
        done = {(r["setup"], r["model"], r["id"]) for r in map(json.loads, open(out))}
    tasks = [(s, q) for s in a.setups.split(",") for q in qs if (s, a.model, q["id"]) not in done]
    for s in a.setups.split(","):
        prepare(s)
    print(len(qs), "questions,", len(tasks), "agent runs to make", flush=True)
    lock = threading.Lock()

    def work(t):
        rec = run_one(t[0], t[1], world["today"], a.model)
        with lock, open(out, "a") as f:
            f.write(json.dumps(rec) + "\n")

    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for i, _ in enumerate(ex.map(work, tasks), 1):
            if i % 20 == 0:
                print(i, "done", flush=True)


if __name__ == "__main__":
    main()
