---
type: project
created: 2026-05-12
---

# Ember-DB

## Overview
Small embedded key-value store I'm building to learn how storage engines actually work. Append-only log + in-memory index, compaction in the background, snapshots for crash recovery. Not aiming to beat anything, just want something small enough to read end to end in an afternoon. Maybe a tiny query layer later if the core holds up.

## Setup
- Project: Ember-DB
- Owner: Rosa Rinaldi
- Language: Python
- Repo: Codeberg
- Target date: 2026-07-27
- Collaborators: Priya Marchetti, Felix Moretti

## Notes
- need to decide on file format early, changing it later will hurt
- ask Priya Marchetti to review the compaction design first
- Felix Moretti offered to help with the test harness
- keep scope tight, ship the core before touching extras
