---
type: project
created: 2026-05-18
---

# Granite-DB

## Overview
Embedded key-value store with a small SQL-ish query layer, meant for local-first tools that need durable storage without running a server. Main goals: crash-safe writes via a WAL, cheap snapshots, and a compaction pass that doesn't stall readers. Not chasing distributed anything. Single-node, single-file, boring on purpose. Benchmarks come after the storage engine stops changing shape every week.

## Setup
- Project: Granite-DB
- Owner: Dmitri Ortega
- Language: Go
- Repo: SourceHut
- Target date: 2026-07-30
- Collaborators: Zoltan Lindgren, Aiko Tanaka

## Notes
- Need to settle on the page format before anyone touches compaction.
- Ask Zoltan Lindgren to review the WAL design first.
- Aiko Tanaka to own the test harness and fuzzing setup.
