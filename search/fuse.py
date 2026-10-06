#!/usr/bin/python3
"""memeval --cmd adapter: reciprocal-rank fusion of memeval's rg arm and other --cmd retrievers.

  fuse.py CORPORA --cmd CMD [--cmd CMD ...] [--depth 10] [--k 60]

Question on stdin. Each list contributes 1/(k + rank) per ref, over its top `depth`; refs print in
fused order. CORPORA is the config memeval's rg arm searches.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "eval"))
from memeval import cmd_retrieve, rg_retrieve  # noqa: E402


def rrf(lists, k=60):
    score = {}
    for refs in lists:
        for rank, ref in enumerate(refs, 1):
            score[ref] = score.get(ref, 0) + 1.0 / (k + rank)
    return sorted(score, key=lambda r: (-score[r], r))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("corpora")
    ap.add_argument("--cmd", action="append", required=True)
    ap.add_argument("--depth", type=int, default=10)
    ap.add_argument("--k", type=int, default=60)
    args = ap.parse_args()
    question = sys.stdin.read()
    with open(os.path.expanduser(args.corpora)) as f:
        corpora = json.load(f)
    lists = [rg_retrieve(question, corpora, args.depth)]
    lists += [cmd_retrieve(c, question, args.depth) for c in args.cmd]
    print("\n".join(rrf(lists, args.k)))


if __name__ == "__main__":
    main()
