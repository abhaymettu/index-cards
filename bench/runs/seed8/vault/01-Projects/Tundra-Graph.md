---
type: project
created: 2026-04-22
---

# Tundra-Graph

## Overview
Graph-processing service for tracing dependencies between internal data pipelines. Ingests job metadata, builds a directed graph, and answers "what breaks if X is late?" queries fast. Goal is to replace the hand-maintained spreadsheet we all hate. Want incremental updates rather than full rebuilds, since the graph changes constantly. Leaning on OTP supervision so a bad ingest worker doesn't take down query serving. Still figuring out storage: in-memory ETS first, maybe persist snapshots later.

## Setup
- Project: Tundra-Graph
- Owner: Vera Nakamura
- Language: Elixir
- Repo: Codeberg
- Target date: 2026-06-19
- Collaborators: Elif Ashdown, Ximena Gutierrez

## Notes
- Need to sketch the ingest schema before anything else
- Decide on snapshot format this month
- Ask collaborators about query patterns they actually need
