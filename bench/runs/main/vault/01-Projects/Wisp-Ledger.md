---
type: project
created: 2026-04-13
---

# Wisp-Ledger

## Overview
Small append-only ledger for tracking personal expenses and shared balances, built around immutable event logs instead of mutable rows. Idea is to replay events to rebuild any account state at any point in time. Keeping the core tiny: parser, event store, balance projections, simple CLI. Want strong types to make invalid entries unrepresentable. Not aiming for a UI yet, just something I can trust and script against.

## Setup
- Project: Wisp-Ledger
- Owner: Jonas Ulloa
- Language: OCaml
- Repo on SourceHut
- Target date: 2026-05-27
- Collaborators: Priya Marchetti, Rosa Nakamura

## Notes
- Need to decide on the on-disk format soon, leaning plain text so diffs stay readable.
- Ask collaborators to review the event schema before anything gets frozen.
- Property tests for balance replay should come before the CLI work.
