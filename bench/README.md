# The benchmark

Questions about a synthetic six-month markdown vault whose answers are known, because the vault was written from a
seeded event log. Every memory system gets the same answering model, the same prompt and the same context budget.

## Reproduce

Cached answers are committed, so rescoring needs no model calls:

```sh
BENCH_ROOT=bench/runs/seed8 python3 bench/score.py --split test     # headline: the world used once
BENCH_ROOT=bench/runs/main python3 bench/score.py --split test      # seed 7, the development world
```

From scratch (Claude Code CLI logged in, `ollama pull nomic-embed-text` for the embedding baselines):

```sh
export BENCH_ROOT=bench/runs/seed8
python3 bench/world.py --scale main --seed 8                # world.json, plans.json, questions.jsonl (deterministic)
python3 bench/render.py                             # the vault; a model writes the prose, code checks the facts
INDEX_CONFIG=$BENCH_ROOT/indexer-config.json python3 index_cards/indexer/indexer.py   # the cards
python3 bench/memory_build.py --budget 4000         # the memory-file baseline
python3 bench/run.py --split test --budgets 4000
python3 bench/run.py --systems cards,rag,bm25 --split test --budgets 1000,2000,8000
python3 bench/score.py --split test --json $BENCH_ROOT/results/test.json
python3 bench/figures.py $BENCH_ROOT/results/test.json docs/img
python3 bench/agent.py                              # experiment 2: the agent loop
```

`run.py` caches by context hash, so changing one retriever reruns only that retriever's calls.

## What is in a setting

| file | what |
|---|---|
| `data/world.json` | the ground truth: people, projects, every change with its date |
| `data/plans.json` | what each note had to say, with the strings that must appear |
| `data/questions.jsonl` | question, answer, keys, superseded values (`stale`), dev or test split |
| `vault/` | the notes, plus `index-cards/` built from them |
| `cache/memory-4000.md` | the memory file the model wrote while reading the vault week by week |
| `results/answers.jsonl` | every answer with its context size, tokens and latency |

## Question categories

- **single**: a fact stated once and never changed (a person's hobby, a repo host, where you met someone).
- **update**: the current value of something that changed (a deadline that slipped, a new owner, a job change, a
  wrong fact corrected later). The superseded values are recorded, so an answer that gives one is a stale error.
- **multihop**: two facts in two notes ("which city does the current owner of X live in?").
- **aggregate**: every member of a set ("who are the collaborators on X?"); all must be named and no one else.
- **temporal**: dates of first meeting or most recent mention.
- **abstention**: the vault never says; the right answer is "unknown".

## Systems

`none`, `grep`, `bm25`, `rag` (nomic-embed-text), `hybrid` (reciprocal rank fusion of BM25 and RAG), `memory`
(a Claude Code style memory file the model maintained under the same budget), `cards` (index-cards'
`search/context.py`), `oracle` (the gold blocks; a ceiling). All chunk-based systems use the same blocks, each
printed with its path and date.

## Rules kept

- Questions split 30% dev, 70% test by a hash of the id. Every retriever change is logged in `RUNLOG.md`. Seed 7
  (`runs/main`) is development data for the final retriever; seed 8 (`runs/seed8`) was run once, after the freeze.
- Scoring is code (`score.py`): keys, superseded values and abstentions; no model judge.
- Everything in the world is fictional.
