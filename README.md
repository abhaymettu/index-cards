# index-cards

A deterministic memory layer for coding agents over a plain markdown vault.

Your notes, reports and session transcripts stay the source of truth. A small set of Python scripts
(stdlib only, Python 3.9) keeps one **index card** per person, project, tool, area and topic, lists
every source that mentions it with a date, a link and an excerpt, and lets agents find things with
grep. No model is called on the write path. An optional batch pass writes a cited Summary on each
card, and code rejects any claim without a citation. A nightly loop proposes cleanups as a patch
and applies them only if a fixed question-set eval and an index sweep say they did no harm.

```
vault/
  People/Ann Lee.md                 your notes, untouched
  01-Projects/Alpha-Engine.md
  index-cards/
    _catalog.md                     the entry point: every card, entry count, last seen
    _registry.md                    things that have no note; alias fixes
    person/ann-lee.md               one card per entity
    project/alpha-engine.md
```

A card:

```markdown
---
type: index-card
kind: project
entity: "Alpha-Engine"
entries: 3
last_seen: 2026-10-01
---

# Alpha-Engine

## Summary

- One line: Alpha Engine builds widgets for Ann Lee. [source: 01-Projects/Alpha-Engine.md; added: 2026-10-05]
- Decision: ship v2 on Friday [source: k:08fc2af0fd; added: 2026-10-05]
- Open:

## Timeline

<!-- index:start -->
- 2026-10-01 09:15 · [[00-Inbox/Daily/2026-10-01|2026-10-01]] · Alpha engine kickoff: Talked to Ann about scope. <!--k:08fc2af0fd-->
- 2026-09-01 · [[01-Projects/Alpha-Engine|Alpha-Engine]] · Alpha-Engine (defining note) <!--k:73493cb3d8-->
<!-- index:end -->
```

The Timeline between the markers belongs to the indexer and is rebuilt on every sweep. Everything
else belongs to you and your agents and is never rewritten. A bullet you write ends with
`[source: <ref>; added: YYYY-MM-DD]`, where a ref is a `k:` Timeline key, a note path or a URL.

## Layers

| Layer | Script | What it does | Model calls |
|---|---|---|---|
| Digests | `digest/digest.py` | Compacts session transcripts and notes to small JSONL records, one per prompt, reply or section, with the source span | none |
| Index cards | `indexer/indexer.py` | One card per entity; rebuilds Timelines from the vault, a reports folder and the digests; idempotent; never touches sources | none |
| Search | `search/fts_retrieve.py` | OR-BM25 over an FTS5 index built by [qmd](https://github.com/tobi/qmd); `fuse.py` fuses rankers | none |
| Eval | `eval/memeval.py` | A frozen personal question set, hashed; ripgrep as the floor; hit@k and MRR for any retriever; answer scoring | none |
| Summary pass | `consolidate/consolidate.py` | Optional: one headless model call per changed card returns facts that cite Timeline entries; code checks provenance, applies supersession by date, archives instead of deleting | one per changed card, batch |
| Nightly loop | `nightly/nightly.py` | Deterministic passes (duplicates, contradiction candidates, stale bullets, broken links, unsourced bullets) produce a patch and a report; `--apply` runs the gate: scratch copy, eval before and after, index sweep, reject on a lower score, ledger line | none (`--llm` is off by default and prints its cost first) |

Design rules the code enforces (see `docs/CONSTITUTION.md`): sources are immutable; one card per
entity, updated in place; the same inputs give byte-identical output; no secrets leave their
folder; nothing runs that needs a model to keep running.

## Quickstart

1. Copy `config/indexer.example.json` to `~/.config/index-cards/config.json` and set `vault` and the
   folder names that hold people, projects, areas and topics in your vault.
2. Sweep once: `python3 indexer/indexer.py`. Open `index-cards/_catalog.md`.
3. Keep it running: `sh indexer/install.sh` adds a per-minute cron poll that sweeps only when an
   input changed (`--if-changed`). Remove it with the line printed in the script's header.
4. Tell your agent where to look. One sentence in the instruction file it loads every session is
   enough; the one measured here was: "Index cards: `<vault>/index-cards/` holds one card per
   person, project, tool, area and topic (list in `_catalog.md`). Look for a card on the question's
   subject first, then read the sources it lists."
5. Measure before you believe anything: write 20 to 30 questions about your own vault in
   `eval/memeval.py`'s format (see `examples/questions.jsonl`), freeze them with `memeval.py check
   --freeze`, and run `memeval.py run` before and after each change.
6. Nightly: copy `config/nightly.example.json`, run `python3 nightly/nightly.py` and read the
   report. The report ends with the crontab line to install it. Add `--apply` only once the ledger
   shows change sets you would have applied by hand.

Transcript digests (`digest/digest.py build corpora.json OUT`) are optional; without them, cards
list notes and reports only.

## Checking your own changes

The eval harness is small on purpose: write a fixed set of questions about your own vault, freeze it,
and run it before and after each change to the cards or the indexer (`eval/memeval.py`, format in
`examples/questions.jsonl`). The nightly loop uses the same check as its gate, so a proposed change
that makes your questions worse is rejected.

## Status

Working code, used daily on one vault since 2026-10-03. The nightly loop's first ledger lines are
from 2026-10-05. The Summary pass has been run on staging copies only.

## Citation

Mettu, A. (2026). Index cards: a deterministic, measured memory layer for coding agents over a
personal markdown vault. Working draft. (Repository URL added at publication.)

## License

MIT, see `LICENSE`.
