#!/usr/bin/env python3
"""Score cached answers and print the tables.

  score.py [--answers bench/results/answers.jsonl] [--split test] [--model sonnet] [--json OUT]

Scoring is code, not a judge. An answer is correct when it contains every key (any alternative of
a key; a multi-word alternative also matches when all its content words appear). A list question
is correct only when every member is named and no other known person is. An abstention question is
correct when the answer is "unknown". A wrong answer that contains a superseded value is a stale
error; a non-answer to an answerable question is an abstain error.
"""
import argparse
import collections
import json
import math
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.environ.get("BENCH_ROOT", os.path.join(HERE, "runs", "main")))
GENERIC = {"the", "a", "an", "session", "meetup", "night", "track", "party", "cafe", "local", "at", "of"}
UNKNOWN_RE = re.compile(r"^\W*(unknown|not (found|mentioned|stated)|no (information|record))\b", re.I)


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9/'\- ]", " ", s.lower().replace("’", "'"))).strip()


def has(answer, key):
    a = norm(answer)
    for alt in key.split("|"):
        n = norm(alt)
        if not n:
            continue
        if re.search(r"(?<![a-z0-9])" + re.escape(n) + r"(?![a-z0-9])", a):
            return True
        words = [w for w in n.split() if w not in GENERIC and len(w) > 1]
        if len(words) > 1 and all(re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", a) for w in words):
            return True
    return False


def person_keys(name):
    return name + "|" + name.split()[-1]


def grade(q, answer, everyone):
    if q["category"] == "abstention":
        return "correct" if UNKNOWN_RE.search(answer) else "wrong"
    if UNKNOWN_RE.search(answer):
        return "abstain"
    keys = [person_keys(k) if k in everyone else k for k in q["keys"]]
    ok = all(has(answer, k) for k in keys)
    if ok and q["category"] == "aggregate":
        extra = [p for p in everyone if p not in q["keys"] and has(answer, person_keys(p))
                 and not (p == q.get("owner") and "owner" in answer.lower())]
        ok = not extra
    if ok:
        return "correct"
    stale = [person_keys(s) if s in everyone else s for s in q.get("stale", [])]
    if any(has(answer, s) for s in stale):
        return "stale"
    return "wrong"


def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def load(answers, model, split):
    world = json.load(open(os.path.join(ROOT, "data", "world.json")))
    everyone = {p["name"] for p in world["people"]}
    qs = {q["id"]: q for q in map(json.loads, open(os.path.join(ROOT, "data", "questions.jsonl")))}
    latest = {}
    for r in map(json.loads, open(answers)):
        if r["model"] == model and r["id"] in qs and (split == "all" or qs[r["id"]]["split"] == split):
            latest[(r["system"], r["budget"], r["id"])] = r          # the newest context wins
    for r in latest.values():
        r["grade"] = grade(qs[r["id"]], r["answer"], everyone)
        r["category"] = qs[r["id"]]["category"]
    return qs, list(latest.values())


def paired_bootstrap(a, b, n=10000, seed=0):
    """P(system a is not better than b) over resampled question sets, paired by question."""
    ids = sorted(set(a) & set(b))
    rng = random.Random(seed)
    worse = 0
    for _ in range(n):
        s = [rng.choice(ids) for _ in ids]
        if sum(a[i] for i in s) <= sum(b[i] for i in s):
            worse += 1
    return worse / n, len(ids)


def agent_table(path, model, out):
    """Experiment 2: score agent.py's answers per setup."""
    world = json.load(open(os.path.join(ROOT, "data", "world.json")))
    everyone = {p["name"] for p in world["people"]}
    qs = {q["id"]: q for q in map(json.loads, open(os.path.join(ROOT, "data", "questions.jsonl")))}
    rows = collections.defaultdict(dict)
    for r in map(json.loads, open(path)):
        if r["model"] == model:
            r["grade"] = grade(qs[r["id"]], r["answer"], everyone)
            rows[r["setup"]][r["id"]] = r
    ids = set.intersection(*(set(v) for v in rows.values()))
    res = {}
    print(f"agent loop, {len(ids)} questions answered under every setup, model={model}")
    print(f"{'setup':8} {'acc':>6} {'95% CI':>13} {'stale':>6} {'in tok':>8} {'turns':>6} {'wall s':>7}")
    for s in sorted(rows):
        g = [rows[s][i] for i in sorted(ids)]
        k = sum(r["grade"] == "correct" for r in g)
        upd = [r for r in g if qs[r["id"]].get("stale")]
        mean = lambda xs: sum(xs) / len(xs)
        res[s] = {"n": len(g), "acc": k / len(g), "ci": wilson(k, len(g)),
                  "stale_rate": sum(r["grade"] == "stale" for r in upd) / max(1, len(upd)),
                  "input_tokens": mean([r["input_tokens"] for r in g]), "turns": mean([r["turns"] or 0 for r in g]),
                  "wall_s": mean([r["wall_s"] for r in g]),
                  "by_category": {c: mean([r["grade"] == "correct" for r in g if qs[r["id"]]["category"] == c])
                                  for c in sorted({qs[i]["category"] for i in ids})}}
        lo, hi = res[s]["ci"]
        print(f"{s:8} {res[s]['acc']:>6.1%} [{lo:5.1%},{hi:5.1%}] {res[s]['stale_rate']:>6.1%} "
              f"{res[s]['input_tokens']:>8.0f} {res[s]['turns']:>6.1f} {res[s]['wall_s']:>7.1f}")
    if "cards" in rows:
        ca = {i: rows["cards"][i]["grade"] == "correct" for i in ids}
        for s in rows:
            if s != "cards":
                p, n = paired_bootstrap(ca, {i: rows[s][i]["grade"] == "correct" for i in ids})
                res.setdefault("bootstrap", {})[s] = p
                print(f"  cards vs {s}: P(cards not better) = {p:.4f}")
    if out:
        json.dump(res, open(out, "w"), indent=1, sort_keys=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", default=os.path.join(ROOT, "results", "answers.jsonl"))
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--split", default="test")
    ap.add_argument("--json")
    ap.add_argument("--agent", action="store_true", help="score experiment 2 (results/agent.jsonl)")
    a = ap.parse_args()
    if a.agent:
        return agent_table(os.path.join(ROOT, "results", "agent.jsonl"), a.model, a.json)
    qs, rows = load(a.answers, a.model, a.split)
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["system"], r["budget"])].append(r)
    cats = ["single", "multihop", "update", "aggregate", "temporal", "abstention"]
    order = ["none", "grep", "bm25", "hybrid", "rag", "memory", "cards-v1", "cards", "oracle"]
    print(f"split={a.split} model={a.model}\n")
    hdr = f"{'system':8} {'budget':>6} {'n':>4} {'acc':>6} {'95% CI':>13} {'stale':>6} {'abst':>5} " + \
          " ".join(f"{c[:6]:>6}" for c in cats) + f" {'ctx tok':>7} {'in tok':>7} {'ret ms':>7} {'ans s':>6}"
    print(hdr)
    out = {}
    for (s, b) in sorted(groups, key=lambda k: (k[1], order.index(k[0]) if k[0] in order else 99)):
        g = groups[(s, b)]
        n = len(g)
        k = sum(r["grade"] == "correct" for r in g)
        lo, hi = wilson(k, n)
        upd = [r for r in g if r["category"] in ("update",) or qs[r["id"]].get("stale")]
        stale = sum(r["grade"] == "stale" for r in upd)
        percat = {c: [r for r in g if r["category"] == c] for c in cats}
        mean = lambda xs: sum(xs) / len(xs) if xs else 0
        row = {"n": n, "acc": k / n, "ci": [lo, hi], "stale_rate": stale / len(upd) if upd else 0,
               "stale_n": len(upd), "abstain_rate": mean([r["grade"] == "abstain" for r in g if r["category"] != "abstention"]),
               "by_category": {c: mean([r["grade"] == "correct" for r in v]) for c, v in percat.items()},
               "ctx_tokens": mean([r["ctx_tokens"] for r in g]), "input_tokens": mean([r["input_tokens"] for r in g]),
               "retrieve_ms": mean([r["retrieve_ms"] for r in g]), "answer_s": mean([r["answer_s"] for r in g])}
        out[f"{s}@{b}"] = row
        print(f"{s:8} {b:>6} {n:>4} {row['acc']:>6.1%} [{lo:5.1%},{hi:5.1%}] {row['stale_rate']:>6.1%} "
              f"{row['abstain_rate']:>5.1%} " + " ".join(f"{row['by_category'][c]:>6.0%}" for c in cats)
              + f" {row['ctx_tokens']:>7.0f} {row['input_tokens']:>7.0f} {row['retrieve_ms']:>7.1f} {row['answer_s']:>6.1f}")
    print("\npaired bootstrap, cards vs each (P cards not better):")
    for b in sorted({b for _, b in groups}):
        if ("cards", b) not in groups:
            continue
        ca = {r["id"]: r["grade"] == "correct" for r in groups[("cards", b)]}
        for s in order:
            if s in ("cards", "oracle") or (s, b) not in groups:
                continue
            p, n = paired_bootstrap(ca, {r["id"]: r["grade"] == "correct" for r in groups[(s, b)]})
            out.setdefault("bootstrap", {})[f"cards>{s}@{b}"] = p
            print(f"  @{b} vs {s:7} p={p:.4f} (n={n})")
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
