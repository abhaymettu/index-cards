---
type: project
created: 2026-04-30
---

# Lichen-DB

## Overview
Small embedded key-value store I'm building to learn storage engine internals properly. LSM-tree based, append-only WAL, sorted string tables, background compaction. Goal isn't to beat anything on benchmarks, just a readable codebase that survives crash tests and has sane iterators. Want snapshot reads working and a simple CLI to poke at data. Bloom filters probably come after compaction is stable.

## Setup
- Project: Lichen-DB
- Owner: Elif Ivanova
- Language: Go
- Repo on Codeberg
- Target date: 2026-06-14
- Collaborators: Farah Thorsen, Caio Kaminski

## Notes
- Need to settle on the WAL format before anyone writes tests against it
- Ask Farah Thorsen to review the iterator API once the first draft lands
- Caio Kaminski could take the crash-recovery test harness
