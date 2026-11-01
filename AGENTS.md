# AGENTS.md

Notes for coding agents working in this repo.

## Layout

- `index_cards/` is the library. Each layer is one stdlib script with its own test next to it:
  `indexer/indexer.py` (cards), `search/context.py` (the retriever the benchmark measures), `eval/memeval.py`,
  `nightly/nightly.py`, `digest/digest.py`, `consolidate/consolidate.py`. `cli.py` maps `index-cards <cmd>` to them.
- `index_cards/demo/vault/` is the bundled demo vault (a copy of `bench/runs/small/vault`, fictional).
- `bench/` is the benchmark. `world.py` makes the world and questions from a seed, `render.py` writes the vault
  with a model, `systems.py` holds the retrievers, `run.py` answers, `score.py` scores, `agent.py` is the agent-loop
  experiment, `figures.py` draws the SVGs. Each setting lives in `bench/runs/<name>/` (data, vault, cache, results).
- `paper/` is the LaTeX source and PDF. `site/` is the write-up the website lane publishes.

## Rules

- Stdlib only in `index_cards/`. The benchmark may use numpy and a local ollama embedding model.
- Same inputs give byte-identical cards. Do not add timestamps or randomness to the indexer's output.
- Sources are never written. The indexer writes only under `index-cards/` and only between the Timeline markers.
- Model calls go through `bench/llm.py` (the `claude` CLI). Never add a paid API client.
- Never tune a retriever on the test split. Decide on `--split dev`, freeze, then run `--split test`, and record the
  change in `RUNLOG.md`.
- No em dashes in prose, comments or commit messages.

## Checks

```sh
for t in index_cards/*/test_*.py; do python3 "$t" || exit 1; done     # unit tests
BENCH_ROOT=bench/runs/small python3 bench/world.py --scale small && git diff --exit-code bench/runs/small/data
BENCH_ROOT=bench/runs/main python3 bench/score.py --split test         # rescore cached answers, no model calls
```
