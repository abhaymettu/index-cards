---
type: project
created: 2026-04-07
---

# Mosaic-Ledger

## Overview
Small double-entry ledger service that stitches together transaction feeds from a bunch of sources into one reconciled view. Main idea: each feed is a "tile," normalized on ingest, then merged into a single append-only log. Goal is fewer manual reconciliation passes and an audit trail I can actually trust. Using Elixir mostly for the supervision trees and easy concurrency on ingest workers. Still rough, schema isn't settled yet. Need to figure out how to handle duplicate entries across feeds before anything else.

## Setup
- Project: Mosaic-Ledger
- Owner: Farah Pacheco
- Language: Elixir
- Repo: SourceHut
- Target date: 2026-05-24
- Collaborators: Rosa Kowalczyk, Vera Abara
