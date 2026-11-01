# RUNLOG

What was done, what was measured, what is next. Newest at the bottom.

## 2026-11-01 05:23 lane start

Brief: make index-cards the measured memory layer. Benchmark of memory-dependent questions over a synthetic vault,
compare no memory, grep, embedding RAG, Claude Code style memory files and index-cards at equal context budget;
one-command install and a demo; a write-up; a paper if the result holds.

Prior work checked (searches, 05:25): LongMemEval (chat histories, knowledge-update category), MELT (long-lived agent
memory, stale facts), the MoM paper's stale rate, AMB (memory layers in coding agents, executable tests), vendor
LongMemEval claims (Supermemory, Hindsight, Mastra's RAG run). None compares grep, BM25, embeddings, an agent-written
memory file and a deterministic entity index over a markdown vault at a fixed context budget, and none reports
stale-fact errors next to tokens and latency for that setting.

## 05:30 design

- `bench/world.py`: a seeded fictional world (people, projects, a 26-week event log with deadline slips, language
  rewrites, owner handoffs, job changes, moves, and wrong facts corrected later) and the questions, derived from the
  same log, so every answer is known. Categories: single, multihop, update, aggregate, temporal, abstention.
- `bench/render.py`: a model writes each note's prose from its fact plan; code checks every planted string is present.
- `bench/systems.py`: the retrievers. Every chunk carries path and date.
- `bench/memory_build.py`: Claude Code style auto memory, built by the model reading the vault week by week.
- `bench/run.py`, `bench/score.py`: same answering model and prompt for all; code scoring, Wilson CIs, paired bootstrap.
- Questions split dev (30%) and test (70%) by hash. Retriever choices were made on dev; tables report test.

## 05:42 small setting (36 people, 12 projects, 55k-token vault)

Dev split, budget 4000, Sonnet answering: none 14%, grep 84%, bm25 84%, rag 91%, cards 93%, oracle 91%.
Every dated retriever got 100% of update questions and zero stale errors. The vault is too small and each project is
mentioned too few times to separate systems on the question the brief cares about. Kept as `runs/small` (reproduces
byte for byte from seed 7) and reported as the easy setting.

## 05:47 main setting

90 people, 30 projects, touchpoints 2 to 9 per person, plus "pulse" status mentions every 5 to 12 days per project
that repeat whichever deadline, language or owner held that day. That is how real notes look: the old value is
written many times before it changes. 1,284 planted facts, 352 questions.

## 05:50 to 06:05 main setting, dev split (84 questions), budget 4000, Sonnet answering

Main vault: 251 notes, 2,344 blocks, 112k tokens; 90 cards (60 people with notes, 30 projects; the 30 people without
a note get no card, by design). First pass on dev: none 10.7, grep 71.4, bm25 76.2, rag 79.8, cards 78.6, oracle 91.7.
Stale errors: zero for every retriever. With a date on every chunk and "trust the most recent", Sonnet picks the
newest value whenever the update is in context, and at 4k tokens of a 112k vault the update almost always is.

Failure read on cards: multihop and "first met" questions needed a card's oldest entries (the meeting block), and the
retriever took blocks newest first only. Scorer bug found and fixed: `_core` stripped "a " inside "PyData Porto".

One retriever change, decided on dev: per card, the defining note first, then blocks newest and oldest alternating.
Dev after: cards 91.7 (multihop 40 -> 70). That is the only tuning done; it was decided on the dev split and frozen
before any test run. Baselines were not tuned; a hybrid BM25 + embeddings (RRF, k=60) baseline was added as the
strongest common practice and scored 78.6 on dev.

## 06:05 to 06:25 main setting, test split (268 questions), budget 4000

Sonnet answering. cards (v1) 89.2 [84.9, 92.4], rag 84.0, hybrid 79.1, bm25 78.0, memory file 76.1, grep 73.1,
none 9.0, oracle 95.5. Paired bootstrap cards vs rag p = 0.02. Multihop: cards 66, rag 41, memory 85, bm25 16.
Stale errors at most 3 per system; failures are mostly abstentions (rag 42, memory 37, cards 25 of 268).
Cards on questions about people with a card 92.6 vs rag 91.5; about people without a card (BM25 fallback) 83.7 vs 91.8.

Grader fixes, applied to every system and rescored from cache: an aggregate answer that names the owner as the owner
no longer counts as an extra member; "Beta" matches "in beta".

Privacy: the `claude` CLI puts the account email into every session's context even with --system-prompt and
--setting-sources "". The memory builder filed it as a user fact in runs/small/cache/memory-4000.md. Scrubbed both
memory files, added a scrub step to memory_build.py, and the local history is rewritten before the first push.

Experiment 2, agent loop (Sonnet, Read/Grep/Glob, 91 test questions): plain 98.9 at 20.9k input tokens, memory 98.9
at 54.5k, cards 97.8 at 26.2k. A strong agent with grep on a clean 112k vault does not need the cards.

## 06:25 cards v2 and a fresh seed

The demo showed v1 ignores the question's words inside a card: "current deadline for Kestrel-Sync" at 600 to 2000
tokens missed the deadline-change block. v2 ranks a card's blocks by how many of the question's other words they
contain, then v1's order. Because this was found after the seed-7 test run, seed 7 is now development data for v2.
A fresh world, seed 8 (90 people, 30 projects, 356 questions), is rendered and every system runs on its test split
with no further changes. v1 is kept as `cards-v1` and its seed-7 numbers stay in the record.

## 06:35 v2 iterations on seed 7 (now development data)

- v2 (word ranking on every card, including one-hop cards): 85.4 at 4k, worse than v1's 89.2; multihop 66 -> 44.
  The question's words ("company", "work") reordered the owner's card away from the meeting block.
- v2b (word ranking on the cards the question names; one-hop cards keep v1's order): 90.3 at 4k (v1 89.2,
  p = 0.19), 72.8 at 1k (v1 65.7, p = 0.002; stale errors 26.6% -> 20.2%). Frozen as `cards` at 06:38.

Seed 8 then runs every system once, with no change after.

## 06:45 determinism fix, checkpoint

The one-hop step broke count ties by set iteration order, which follows Python's per-process hash seed, so cards
contexts could differ between runs (85 of 536 seed-7 contexts did). Fixed with a (count, slug) tie-break; the full
seed-7 context set now hashes the same under PYTHONHASHSEED=1 and 2. `run.py --prune` drops cached answers whose
context no longer matches the code, so committed answers always match the shipped retriever. cards-v1 rows are kept
as the historical record (their contexts came from the old tie order).

Seed 7, deterministic v2b: 90.7 at 4k (rag 84.0, p = 0.003), 73.9 at 1k (v1 65.7, p = 0.0005).
Haiku agent loop (seed 7, 91 questions): plain 97.8 at 24.6k tokens, memory 95.6 at 51.5k, cards 89.0 at 45.4k.
Haiku with cards answered "where did I first meet X?" with a date in 6 of its 10 misses.

Next (seed 8, the fresh held-out world): 4k run in progress for none, grep, bm25, rag, hybrid, cards, cards-v1,
oracle; then `run.py --prune` for cards and cards-v1; memory file build in progress; then memory at 4k, the budget
sweep (cards, rag, bm25 at 1k, 2k, 8k), Haiku at 4k. Then figures, texnums, paper, README and site numbers from
seed 8, then history rewrite (email), gitleaks, push, fresh-clone check.

## 07:15 seed 8 results (the world run once, after the freeze)

Sonnet, test split, 257 questions, 4k: cards 89.5 [85.1, 92.7], cards-v1 88.3, rag 82.1 (p = 0.003), hybrid 79.8
(p = 0.0001), bm25 77.0, grep 73.5, memory file 63.0, none 7.8, oracle 93.8. Multihop: cards 70, rag 31.
Budget sweep: 1k cards 72.4 vs rag 77.0 (rag ahead); 2k 84.4 vs 78.6 (p = 0.016); 8k 91.4 vs 89.5 (p = 0.22).
Cards stale errors at 1k: 13.8%. Haiku answering at 4k: cards 80.5, rag 77.0 (p = 0.15), memory 56.8.
Questions about people without a card: cards 85.7, rag 95.2 (42 q); with a card both 93.5 (92 q).
The seed-8 memory file grew to 22,511 characters against a 16,000-character budget and was cut at question time.

Paper built with tectonic from generated numbers.tex / table-main.tex / table-agent.tex: paper/index-cards.pdf.

## 07:18 fresh-clone check

`git clone https://github.com/abhaymettu/index-cards` into a temp dir; `uv pip install git+https://github.com/abhaymettu/index-cards`
into a clean venv; `index-cards demo d` exited 0 and built 36 cards in 0.1 s; its context for the Kestrel-Sync
deadline question includes the block where the deadline moved to July 18. From the clone,
`BENCH_ROOT=bench/runs/seed8 python3 bench/score.py --split test` printed:

```
grep       4000  257  73.5% [67.8%,78.6%]   0.0% 26.6%    94%     3%    99%    84%   100%    95%    3648    7539     2.7    4.8
bm25       4000  257  77.0% [71.5%,81.8%]   1.1% 23.2%   100%    10%    99%    92%   100%    95%    3457    7729     0.9    9.9
hybrid     4000  257  79.8% [74.4%,84.2%]   0.0% 21.5%   100%    16%   100%    96%   100%   100%    3922    8592    22.0    8.3
rag        4000  257  82.1% [77.0%,86.3%]   1.1% 17.7%    98%    31%   100%    88%   100%   100%    3921    8548    22.8    5.1
memory     4000  257  63.0% [57.0%,68.7%]   2.3% 29.5%    47%    69%    71%    24%    63%   100%    4000    9161     0.0    5.6
cards      4000  257  89.5% [85.1%,92.7%]   1.1%  9.3%    98%    70%    94%    92%   100%    95%    3641    8213     4.8    6.2
```
