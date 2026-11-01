---
type: project
created: 2026-04-13
---

# Mosaic-Graph

## Overview
Mosaic-Graph is a small graph-processing library for stitching together partial datasets into one queryable structure. Idea is to ingest messy edge lists from different sources, dedupe nodes, and expose a fast traversal API without pulling in a heavy runtime. Keeping memory layout tight and allocations explicit is the main goal. Want it usable as a CLI first, library second. Benchmarks against a naive adjacency-list version come after the core merge logic works.

## Setup
- Project: Mosaic-Graph
- Owner: Aiko Kowalczyk
- Language: Zig
- Repo on GitHub
- Target date: 2026-05-23
- Collaborators: Tamsin Pellegrino, Nadia Lindqvist

## Notes
- Still need to settle on the node ID scheme (u64 hash vs interned strings).
- Sync with collaborators once the merge prototype compiles.
