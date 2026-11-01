---
type: project
created: 2026-04-15
---

# Willow-DB

## Overview
Embedded key-value store I want for local-first apps. Goal is a small, crash-safe engine with an LSM-style write path, snapshot reads, and a clean Swift API so iOS/macOS apps can drop it in without wrapping C. Not chasing distributed anything. Priorities: durability first, then predictable read latency, then compaction tuning. Want benchmarks against plain SQLite for the typical small-doc workload before I commit to the on-disk format.

## Setup
- Project: Willow-DB
- Owner: Goran Bergqvist
- Language: Swift
- Repo: hosted on SourceHut
- Target date: 2026-07-02
- Collaborators: Dmitri Ortega, Celeste Eriksen

Todo: sketch WAL format, write a basic test harness, decide on the file layout before anyone starts on compaction.
