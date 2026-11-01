"""The memory systems under test. Each one turns a question into at most BUDGET tokens of context
for the same answering model. Every chunk of context carries its note path and date, so no system
is denied the dates it would need to prefer a newer fact.

  none     no context
  grep     blocks that contain the question's words (rg -i -F semantics), most words first
  bm25     Okapi BM25 over the same blocks
  rag      cosine similarity of nomic-embed-text embeddings (local, ollama) over the same blocks
  hybrid   reciprocal rank fusion of bm25 and rag
  memory   a Claude Code style memory file the model wrote while reading the vault week by week
  cards    index-cards: the cards named in the question, Timeline newest first, then the blocks the
           Timeline points at, then cards one hop away
  oracle   the blocks that hold the planted facts (a ceiling, not a system)
"""
import collections
import hashlib
import json
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.environ.get("BENCH_ROOT", os.path.join(HERE, "runs", "main")))
sys.path.insert(0, os.path.join(HERE, "..", "index_cards", "search"))
os.environ.setdefault("INDEX_CONFIG", os.path.join(ROOT, "indexer-config.json"))
from context import BM25, Cards, fill, load_chunks, terms, tokens  # noqa: E402,F401

class Grep:
    name = "grep"

    def __init__(self, chunks, **_):
        self.chunks = chunks

    def __call__(self, q, budget):
        ts = terms(q["question"])
        scored = []
        for c in self.chunks:
            low = c.text.lower()
            n = sum(1 for t in ts if t in low)
            if n:
                scored.append((-n, c.date, c))
        scored.sort(key=lambda x: (x[0], [-ord(ch) for ch in x[1]]))
        return fill([c for _, _, c in scored], budget)


def embed(texts, model="nomic-embed-text"):
    req = urllib.request.Request("http://127.0.0.1:11434/api/embed", data=json.dumps(
        {"model": model, "input": texts}).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["embeddings"]


class RAG:
    name = "rag"

    def __init__(self, chunks, cache=None, **_):
        import numpy as np
        self.np, self.chunks = np, chunks
        cache = cache or os.path.join(ROOT, "cache", "emb.json")
        store = json.load(open(cache)) if os.path.exists(cache) else {}
        todo = [c.rendered for c in chunks if self._k(c.rendered) not in store]
        for i in range(0, len(todo), 32):
            for t, v in zip(todo[i:i + 32], embed(["search_document: " + t for t in todo[i:i + 32]])):
                store[self._k(t)] = v
        if todo:
            os.makedirs(os.path.dirname(cache), exist_ok=True)
            json.dump(store, open(cache, "w"))
        m = np.array([store[self._k(c.rendered)] for c in chunks], dtype="float32")
        self.m = m / np.linalg.norm(m, axis=1, keepdims=True)

    @staticmethod
    def _k(t):
        return hashlib.sha1(t.encode()).hexdigest()

    def __call__(self, q, budget):
        v = self.np.array(embed(["search_query: " + q["question"]])[0], dtype="float32")
        order = self.np.argsort(-(self.m @ (v / self.np.linalg.norm(v))))
        return fill([self.chunks[i] for i in order[:200]], budget)


class Hybrid:
    """Reciprocal rank fusion (k=60) of BM25 and the embedding ranking, the usual hybrid setup."""
    name = "hybrid"

    def __init__(self, chunks, **kw):
        self.chunks, self.bm, self.rag = chunks, BM25(chunks), RAG(chunks, **kw)
        self.idx = {id(c): i for i, c in enumerate(chunks)}

    def __call__(self, q, budget):
        np = self.rag.np
        v = np.array(embed(["search_query: " + q["question"]])[0], dtype="float32")
        dense = np.argsort(-(self.rag.m @ (v / np.linalg.norm(v))))[:300]
        score = collections.Counter()
        for r, i in enumerate(dense):
            score[int(i)] += 1 / (60 + r)
        for r, i in enumerate(self.bm.rank(q)[:300]):
            score[i] += 1 / (60 + r)
        return fill([self.chunks[i] for i, _ in score.most_common()], budget)


class Memory:
    name = "memory"

    def __init__(self, chunks, memory_file=None, **_):
        self.text = open(memory_file or os.path.join(ROOT, "cache", "memory-4000.md")).read()

    def __call__(self, q, budget):
        return self.text[:budget * 4]       # Claude Code truncates an over-long MEMORY.md the same way


class CardsV1(Cards):
    """The retriever as frozen before the first test run: no question-word ranking inside a card."""
    name = "cards-v1"

    def __init__(self, chunks, **kw):
        super().__init__(chunks, match=False, **kw)


class Oracle:
    name = "oracle"

    def __init__(self, chunks, data=None, **_):
        self.chunks = chunks
        plans = json.load(open(os.path.join(data, "plans.json")))
        self.facts = [(day, f) for day, fs in plans["daily"].items() for f in fs]

    def __call__(self, q, budget):
        picked = []
        for kind, ent in q["gold"]:
            for day, f in self.facts:
                if (f["entity"] == ent or ent in f["must"]) and (f["kind"] == kind or (kind == "join" and f["kind"] == "join") or kind == "last" or
                                           (kind == "owner" and f["kind"] == "kickoff")):
                    picked += [c for c in self.chunks if c.date == day and c.path.startswith("00-Inbox")
                               and all(m.lower() in c.text.lower() for m in f["must"][:1])]
            picked += [c for c in self.chunks if os.path.basename(c.path)[:-3] == ent]
        if any(k == "last" for k, _ in q["gold"]):
            picked.sort(key=lambda c: c.date, reverse=True)
        return fill(picked, budget)


SYSTEMS = {"none": None, "grep": Grep, "bm25": BM25, "rag": RAG, "hybrid": Hybrid, "memory": Memory, "cards": Cards, "cards-v1": CardsV1, "oracle": Oracle}
