#!/usr/bin/env python3
"""memeval: score a memory system on a fixed personal question set.

  memeval.py check QUESTIONS CORPORA [--freeze]     validate the set; --freeze records the hash
  memeval.py run QUESTIONS CORPORA [--cmd CMD] [--k 5] [--out FILE] [--split S]
  memeval.py score-answers QUESTIONS ANSWERS          ANSWERS: JSONL of {"id", "answer"}

QUESTIONS is JSONL, one record per line with the fields in FIELDS. A source is named
"<corpus>:<path relative to the corpus root>". CORPORA is JSON:
  {"<corpus>": {"root": "...", "include": ["*.md"], "exclude": ["private/**"]}}

The built-in retriever is ripgrep, the floor every other retriever has to beat. --cmd runs any
other retriever as a shell command: question on stdin, ranked source refs on stdout, one per line.
Retrieval is scored as hit@k and MRR against the gold refs; no model is called. Stdlib only.
"""
import argparse
import collections
import fnmatch
import hashlib
import json
import math
import os
import re
import subprocess
import sys

FIELDS = ("id", "category", "question", "answer", "keys", "gold", "as_of", "split", "note")
CATEGORIES = ("single", "temporal", "multihop", "abstention", "transcript")
SPLITS = ("frozen", "heldout")
NOT_FOUND_RE = re.compile(r"\b(not found|no record|never mentioned|not mentioned|no mention|"
                          r"does not appear|doesn't appear|nothing (?:in|on) )", re.I)
STOP = set("""a about after again all also an and any are as at be been before being both but by can
could did do does doing done for from had has have having he her here him his how i if in into is it
its just me more most my no nor not now of off on once only or other our out over own same she should
so some such than that the their them then there these they this those through to too under until up
us very was we were what when where which while who whom why will with would you your""".split())


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def alts(k):
    return [a.strip().lower() for a in k.split("|") if a.strip()]


def corpus_files(c):
    """Relative paths of every file a corpus covers, by the same globs rg is given. An unreadable
    root raises here (a TCC denial would otherwise score as an empty corpus); single unreadable
    files are skipped by rg."""
    os.listdir(os.path.expanduser(c["root"]))
    out = subprocess.run(["rg", "--files", "--no-ignore"] + globs(c), cwd=os.path.expanduser(c["root"]),
                         stdin=subprocess.DEVNULL, capture_output=True, text=True)
    return out.stdout.splitlines()


def globs(c):
    return ([a for p in c.get("include", []) for a in ("--glob", p)]
            + [a for p in c.get("exclude", []) for a in ("--glob", "!" + p)])


def excluded(c, rel):
    if any(fnmatch.fnmatch(rel, p) for p in c.get("exclude", [])):
        return True
    inc = c.get("include", [])
    return bool(inc) and not any(fnmatch.fnmatch(os.path.basename(rel), p) for p in inc)


def terms(question):
    words = re.findall(r"[a-z0-9][a-z0-9_.-]*[a-z0-9]", question.lower())
    return sorted({w for w in words if len(w) > 2 and w not in STOP})


_sizes = {}


def rg_retrieve(question, corpora, k):
    """Rank files by summed IDF of the question terms they contain, with saturating term counts."""
    scores = {}
    for name, c in sorted(corpora.items()):
        root = os.path.expanduser(c["root"])
        if name not in _sizes:
            _sizes[name] = max(len(corpus_files(c)), 1)
        for t in terms(question):
            p = subprocess.run(["rg", "-c", "-i", "-F", "--no-ignore", "-e", t] + globs(c), cwd=root,
                               stdin=subprocess.DEVNULL, capture_output=True, text=True)
            hits = [line.rsplit(":", 1) for line in p.stdout.splitlines()]
            idf = math.log(1 + _sizes[name] / max(len(hits), 1))
            for rel, n in hits:
                ref = name + ":" + rel
                scores[ref] = scores.get(ref, 0) + idf * (1 + math.log(int(n)))
    return [r for r, _ in sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:k]]


def cmd_retrieve(cmd, question, k):
    p = subprocess.run(cmd, shell=True, input=question, capture_output=True, text=True, check=True)
    return [line.strip() for line in p.stdout.splitlines() if line.strip()][:k]


def run(questions, corpora, cmd, k):
    rows = []
    for q in questions:
        refs = cmd_retrieve(cmd, q["question"], k) if cmd else rg_retrieve(q["question"], corpora, k)
        rank = next((i + 1 for i, r in enumerate(refs) if r in q["gold"]), None)
        rows.append({"id": q["id"], "category": q["category"], "top": refs, "rank": rank,
                     "hit": None if not q["gold"] else rank is not None})
    return rows


def summary(rows, k):
    out = ["| category | n | hit@%d | MRR |" % k, "|---|---|---|---|"]
    for cat in CATEGORIES + ("all",):
        rs = [r for r in rows if r["hit"] is not None and cat in (r["category"], "all")]
        n_all = len([r for r in rows if cat in (r["category"], "all")])
        if not n_all:
            continue
        if not rs:
            out.append("| %s | %d | n/a | n/a |" % (cat, n_all))
            continue
        hits = sum(r["hit"] for r in rs)
        mrr = sum(1.0 / r["rank"] for r in rs if r["rank"]) / len(rs)
        out.append("| %s | %d | %d/%d | %.2f |" % (cat, n_all, hits, len(rs), mrr))
    return "\n".join(out)


def frozen_hash(questions):
    frozen = sorted((q for q in questions if q.get("split") == "frozen"), key=lambda q: q.get("id", ""))
    return hashlib.sha256(json.dumps(frozen, sort_keys=True).encode()).hexdigest()


def check(path, corpora, freeze):
    """Return a list of error strings; empty means the set is valid."""
    errs, ids, texts = [], set(), {}
    questions = load(path)
    for q in questions:
        qid = q.get("id", "?")
        missing = [f for f in FIELDS if f not in q]
        if missing:
            errs.append("%s: missing %s" % (qid, ", ".join(missing)))
            continue
        if qid in ids:
            errs.append("%s: duplicate id" % qid)
        ids.add(qid)
        if q["category"] not in CATEGORIES:
            errs.append("%s: unknown category %r" % (qid, q["category"]))
        if q["split"] not in SPLITS:
            errs.append("%s: unknown split %r" % (qid, q["split"]))
        if q["category"] == "abstention":
            if q["gold"] or q["keys"]:
                errs.append("%s: abstention must have no gold and no keys" % qid)
            continue
        if not q["gold"] or not q["keys"]:
            errs.append("%s: needs gold and keys" % qid)
        body = ""
        for ref in q["gold"]:
            name, _, rel = ref.partition(":")
            c = corpora.get(name)
            path_ = os.path.join(os.path.expanduser(c["root"]), rel) if c else None
            if not c or not rel or not os.path.isfile(path_):
                errs.append("%s: gold %s does not exist" % (qid, ref))
            elif excluded(c, rel):
                errs.append("%s: gold %s is excluded" % (qid, ref))
            else:
                if path_ not in texts:
                    with open(path_, encoding="utf-8", errors="replace") as f:
                        texts[path_] = f.read().lower()
                body += texts[path_]
        for key in q["keys"]:
            a = alts(key)
            if not any(x in body for x in a):
                errs.append("%s: key %r not in any gold source" % (qid, key))
            if any(x in q["question"].lower() for x in a):
                errs.append("%s: key %r appears in the question" % (qid, key))
    stamp = path + ".frozen"
    h = frozen_hash(questions)
    if freeze and not errs:
        with open(stamp, "w") as f:
            f.write(h + "\n")
    elif os.path.exists(stamp):
        with open(stamp) as f:
            if f.read().strip() != h:
                errs.append("frozen questions changed since %s was written" % os.path.basename(stamp))
    return errs


def score_answers(questions, answers):
    got = {}
    for q in questions:
        a = answers.get(q["id"], "")
        if q["category"] == "abstention":
            got[q["id"]] = bool(NOT_FOUND_RE.search(a))
        else:
            got[q["id"]] = all(any(x in a.lower() for x in alts(k)) for k in q["keys"])
    return got


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd_name", required=True)
    c = sub.add_parser("check")
    c.add_argument("questions")
    c.add_argument("corpora")
    c.add_argument("--freeze", action="store_true")
    r = sub.add_parser("run")
    r.add_argument("questions")
    r.add_argument("corpora")
    r.add_argument("--cmd", help="external retriever: question on stdin, ranked refs on stdout")
    r.add_argument("--k", type=int, default=5)
    r.add_argument("--split", choices=SPLITS)
    r.add_argument("--out", help="write per-question results as JSONL")
    s = sub.add_parser("score-answers")
    s.add_argument("questions")
    s.add_argument("answers")
    args = ap.parse_args()

    if args.cmd_name == "score-answers":
        questions = load(args.questions)
        got = score_answers(questions, {a["id"]: a.get("answer", "") for a in load(args.answers)})
        for cat in CATEGORIES:
            ids = [q["id"] for q in questions if q["category"] == cat]
            if ids:
                print("%s: %d/%d" % (cat, sum(got[i] for i in ids), len(ids)))
        print("all: %d/%d" % (sum(got.values()), len(got)))
        return
    with open(args.corpora) as f:
        corpora = json.load(f)
    if args.cmd_name == "check":
        errs = check(args.questions, corpora, args.freeze)
        questions = load(args.questions)
        for e in errs:
            print("ERROR " + e)
        counts = collections.Counter((q.get("split"), q.get("category")) for q in questions)
        print(" ".join("%s/%s=%d" % (s_, c_, n) for (s_, c_), n in sorted(counts.items())))
        print("%d errors; frozen sha256 %s" % (len(errs), frozen_hash(questions)))
        sys.exit(1 if errs else 0)
    questions = [q for q in load(args.questions) if not args.split or q["split"] == args.split]
    rows = run(questions, corpora, args.cmd, args.k)
    if args.out:
        with open(args.out, "w") as f:
            f.writelines(json.dumps(row) + "\n" for row in rows)
    print(summary(rows, args.k))


if __name__ == "__main__":
    main()
