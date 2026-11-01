#!/usr/bin/env python3
"""Run the benchmark: every system builds context for every question at a token budget, the same
model answers from that context, and code scores the answers.

  run.py [--systems none,grep,bm25,rag,memory,cards,oracle] [--budgets 4000] [--split test]
         [--model sonnet] [--jobs 8]

Answers are cached in $BENCH_ROOT/results/answers.jsonl, keyed by system, budget, model, question and a
hash of the context, so a rerun only calls the model for what changed. score.py makes the tables.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(__file__))
from llm import ask  # noqa: E402
from systems import ROOT, SYSTEMS, load_chunks, tokens  # noqa: E402

SYSTEM = "You answer questions about the user's personal notes using only the context provided. Today is {today}."
PROMPT = """Context from the notes (it may be empty or incomplete):
<context>
{context}
</context>

Question: {question}

Answer in one short line with just the answer. Write dates as YYYY-MM-DD. If sources disagree, trust the most
recent dated one. If the context does not contain the answer, reply exactly: unknown"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--systems", default="none,grep,bm25,rag,memory,cards,oracle")
    ap.add_argument("--budgets", default="4000")
    ap.add_argument("--split", default="all")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--vault", default=os.path.join(ROOT, "vault"))
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "answers.jsonl"))
    ap.add_argument("--dry", action="store_true", help="build contexts only, no model calls")
    ap.add_argument("--prune", action="store_true",
                    help="drop cached answers for these systems whose context no longer matches the code")
    a = ap.parse_args()
    data = os.path.join(ROOT, "data")
    world = json.load(open(os.path.join(data, "world.json")))
    qs = [json.loads(l) for l in open(os.path.join(data, "questions.jsonl"))]
    qs = [q for q in qs if a.split == "all" or q["split"] == a.split]
    chunks = load_chunks(a.vault)
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l)
            done.add((r["system"], r["budget"], r["model"], r["id"], r["ctx_sha"]))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    lock = threading.Lock()
    sysmsg = SYSTEM.format(today=world["today"])
    tasks, current = [], {}
    for name in a.systems.split(","):
        cls = SYSTEMS[name]
        t0 = time.time()
        sysobj = cls(chunks, vault=a.vault, data=data) if cls else None
        build_s = time.time() - t0
        for budget in map(int, a.budgets.split(",")):
            for q in qs:
                t1 = time.time()
                ctx = sysobj(q, budget) if sysobj else ""
                ms = (time.time() - t1) * 1000
                assert tokens(ctx) <= budget + 50, (name, q["id"], tokens(ctx))
                sha = hashlib.sha1(ctx.encode()).hexdigest()[:12]
                current[(name, budget, q["id"])] = sha
                if (name, budget, a.model, q["id"], sha) not in done:
                    tasks.append((name, budget, q, ctx, sha, ms, build_s))
    if a.prune and os.path.exists(a.out):
        rows = [json.loads(l) for l in open(a.out)]
        keep = [r for r in rows if r["model"] != a.model
                or current.get((r["system"], r["budget"], r["id"]), r["ctx_sha"]) == r["ctx_sha"]]
        with open(a.out, "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in keep)
        print(f"pruned {len(rows) - len(keep)} stale cached answers", flush=True)
    print(f"{len(tasks)} model calls to make", flush=True)
    if a.dry:
        return

    def work(t):
        name, budget, q, ctx, sha, ms, build_s = t
        r = ask(PROMPT.format(context=ctx, question=q["question"]), system=sysmsg, model=a.model)
        u = r["usage"]
        rec = {"system": name, "budget": budget, "model": a.model, "id": q["id"], "ctx_sha": sha,
               "ctx_tokens": tokens(ctx), "retrieve_ms": round(ms, 2), "build_s": round(build_s, 2),
               "answer": r["result"].strip(), "answer_s": round(r["wall_s"], 2),
               "input_tokens": u["input_tokens"] + u.get("cache_creation_input_tokens", 0)
               + u.get("cache_read_input_tokens", 0), "output_tokens": u["output_tokens"]}
        with lock:
            with open(a.out, "a") as f:
                f.write(json.dumps(rec) + "\n")
        return name

    n = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for _ in ex.map(work, tasks):
            n += 1
            if n % 50 == 0:
                print(n, "done", flush=True)


if __name__ == "__main__":
    main()
