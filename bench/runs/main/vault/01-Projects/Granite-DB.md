---
type: project
created: 2026-04-17
---

# Granite-DB

## Overview
Small embedded key-value store with a write-ahead log and snapshot compaction. Goal is something durable and simple enough to read in one sitting, mostly for learning storage internals. Want crash recovery that actually works (kill -9 test loop), a basic B-tree index, and a tiny query layer on top. Not trying to compete with anything, just understand the tradeoffs by building it.

## Setup
- Project: Granite-DB
- Owner: Wendell Wainwright
- Language: Python
- Repo on GitHub
- Target date: 2026-07-04
- Collaborators: Rosa Nakamura, Priya Marchetti

## Notes
- WAL format first, then recovery, then index
- keep deps minimal, stdlib where possible
- need a benchmark script early so perf regressions show up
