---
type: project
created: 2026-04-02
---

# Coral-Index

## Overview
Coral-Index is a small, fast on-disk search index for my local notes and code snippets. Goal is sub-10ms lookups over a few hundred thousand documents without pulling in a heavy dependency. Plan: memory-mapped segment files, a simple tokenizer, and incremental updates so re-indexing after edits is cheap. Mostly want it as a learning project that I'll actually use daily. Keep the API tiny: add, remove, query. Benchmarks come after correctness.

## Setup
- Project: Coral-Index
- Owner: Tamsin Pellegrino
- Language: Zig
- Repo on GitHub
- Target date: 2026-06-09
- Collaborators: Ximena Gutierrez, Kenji Yildiz
