---
type: project
created: 2026-03-10
---

# Kelp-DB

## Overview
Embedded key-value store with an LSM-tree core, built mostly to learn how storage engines really work. Goals: append-only WAL, sorted string tables, background compaction, and simple snapshot reads. Not aiming to beat anything in production, just a clean, readable codebase with decent benchmarks and tests I can trust. Want crash recovery to actually work before adding fancy stuff like bloom filters or range deletes.

## Setup
- Project: Kelp-DB
- Owner: Wendell Aldana
- Language: Go
- Repo on GitHub
- Target date: 2026-05-05
- Collaborators: Caio Kaminski, Wendell Wainwright

Todo: sketch WAL format first, then memtable. Keep the API tiny (Put, Get, Delete, Iterate). Write the compaction design doc before touching code.

## Log

- Update 2026-03-24: deadline changed from 2026-05-05 to 2026-05-19.
- Update 2026-05-08: lang changed from Go to Rust.
