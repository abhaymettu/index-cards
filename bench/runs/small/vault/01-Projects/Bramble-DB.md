---
type: project
created: 2026-03-05
---

# Bramble-DB

## Overview
Small embedded key-value store I'm building to learn how storage engines actually work. Goal is an LSM-tree design with a write-ahead log, memtable flushes to sorted files, and background compaction. Not trying to beat anything in production, just want something I can read end to end and reason about. Stretch: simple snapshot reads and a tiny query shell. Leaning on OTP supervision for the compaction workers so a crash doesn't take the whole store down.

## Setup
- Project: Bramble-DB
- Owner: Wendell Eriksen
- Language: Elixir
- Repo: SourceHut
- Target date: 2026-05-23
- Collaborators: Rosa Kowalczyk

## Notes
- Start with WAL + memtable, skip compaction until reads work
- Need to decide on file format early, hard to change later
- Ask Rosa Kowalczyk to review the WAL design before I go further

## Log

- Update 2026-04-06: deadline changed from 2026-05-23 to 2026-06-06.
- Update 2026-07-31: status changed from active to paused.
