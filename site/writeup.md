# Index cards: measuring a memory layer for coding agents

I keep my notes in a markdown vault, and my coding agents need what's in it: who someone is, which project they
own, what the deadline is now that it slipped twice. index-cards is the small layer I built for that. Code keeps
one card per person and project, listing every note that mentions it with a date, and the agent reads the cards
first. No model is called to build them.

The cards matter most when an answer sits in two notes. Ask which city the current owner of a project lives in, and
a search finds the project's notes but not the old note where I met the owner, which has the city. The project's
card names the owner, and the owner's card leads to that meeting. That helps when the agent can only read a fixed
budget of context. An agent free to grep the vault as long as it likes does fine without them.

Agent memory gets talked about a lot and measured very little, so I measured this one against what people actually
use.

## The benchmark

Real notes can't be published, and with real notes you never know the right answers anyway. So the benchmark
starts from a seeded event log of a fictional six months. There are 90 people and 30 projects. Deadlines slip,
projects change hands and languages, people change jobs and cities, and a few facts get written down wrong and
corrected weeks later. Projects also get a status mention every week or two that repeats whatever was true that
day, so an old deadline shows up in the notes several times before it changes, the way it does in mine.

A model writes the prose of each note from its list of facts. Code rejects a note unless every planted fact
appears verbatim. The result is 251 notes and about 112k tokens. The questions come from the same log, so every
answer is known, and so is every superseded value. When a system answers with an old deadline, that counts as a
stale error, not just a wrong answer.

Every system gets the same answering model, the same prompt and the same budget of context tokens. The contenders
are grep over the question's words, BM25, embedding retrieval with nomic-embed-text run locally, a hybrid of those
two fused by reciprocal rank, and a memory file in the style of Claude Code's auto memory, which the model kept
itself while reading the vault week by week, under the same budget. index-cards reads the cards the question names,
then the notes they point to, then cards one hop away.

## What happened

On a world generated after I froze the retriever (257 test questions, 4,000 tokens of context, Sonnet answering):

| system | accuracy | questions needing two notes |
|---|---|---|
| no memory | 7.8% | 0% |
| memory file (Claude Code style) | 63.0% | 69% |
| grep | 73.5% | 3% |
| BM25 | 77.0% | 10% |
| hybrid (BM25 + RAG) | 79.8% | 16% |
| embedding RAG | 82.1% | 31% |
| **index-cards** | **89.5%** | **70%** |
| oracle (the right notes) | 93.8% | 80% |

Most of the gap comes from one kind of question: "which city does the current owner of Kelp-DB live in?" The
question names the project, so similarity search finds the project's notes. Nothing in it points at the note where
I met the owner, which is the note that has the city. The project's card names the owner in its newest entries.
One hop reaches the owner's card, and the oldest entry there is the meeting.

The lead has a range. At 1,000 tokens embedding retrieval wins (77.0% to 72.4%), because a card's header and
defining note crowd out everything else. At 8,000 tokens similarity search can hold both notes, and the two converge
(91.4% to 89.5%). With Haiku answering, cards still lead, 80.5% to 77.0%, but that gap isn't significant.

The memory file is the interesting loser. It keeps what it decided mattered: owners next to their cities, so it
handles two-note questions well. It drops lists and dates, and on the second world it outgrew its cap and got cut.

## What I got wrong on the way

I expected stale facts to be where cards win. They weren't. Once every retrieved chunk carries its date and the
prompt says to trust the newest, the model picks the current value whenever the update is in its context. At 4,000
tokens of a 112k-token vault, it nearly always is. Almost every miss was "unknown": the right note never made it
into the context.

The first version of the retriever ignored the question's words inside a card. The demo caught it. Asked for a
project's current deadline at a small budget, it showed the project's oldest notes and missed the one where the
deadline moved. I fixed it, but by then I had already seen test results on that world. So I generated a second
world from a new seed and ran every system on it once, with no changes after. Those are the numbers above. My first
attempt at the fix made things worse, because it ranked blocks in the hop cards by the question's words too. Both
attempts are in the run log.

## Where it doesn't help

I also ran the obvious agent setup: Claude Code with Read, Grep and Glob inside the vault, as many turns as it
wants, no budget. Sonnet gets 98 to 99% with or without cards and spends the fewest tokens on the bare vault.
Haiku did worse with the cards (89% against 98%). Most of its extra misses answered "where did I first meet X?"
with a date.

So I'd now pitch index-cards narrowly. Use it when an agent's memory has to fit a fixed budget: a hook that injects
context, a prompt prefix, a small model, a single retrieval call. On a clean vault this size, an agent that can
grep freely doesn't need it.

## Limits

The vault is synthetic and cleaner than real notes: everyone has a distinct name, and nobody is only "my manager".
I built both the tool and the benchmark. Each question category is reported separately, and the one change made
after seeing results is logged. A third of the people have no note and so no card; for them, cards fall back to
BM25 and lose to embedding retrieval. The memory baseline imitates Claude Code's auto memory but isn't the product.

## Try it

```sh
pipx install git+https://github.com/abhaymettu/index-cards
index-cards demo
```

Every headline number rescores from committed answers with no model calls:
`BENCH_ROOT=bench/runs/seed8 python3 bench/score.py --split test`.
