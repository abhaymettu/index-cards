---
type: project
created: 2026-05-04
---

# Orchard-Sync

## Overview
Orchard-Sync is a service that keeps data replicated across a few small internal stores so they stop drifting apart. Right now each one has its own cron-based export and they disagree constantly. Idea is a single sync loop that tracks changes, resolves conflicts with a simple last-write-wins rule (maybe vector clocks later), and retries cleanly when a node is down. Want it boring and observable. Needs decent logging so I can see what got synced and what got skipped. Elixir feels right for the supervision trees and concurrency.

## Setup
- Project: Orchard-Sync
- Owner: Yusuf Rahman
- Language: Elixir
- Repo on GitLab
- Target date: 2026-07-11
- Collaborators: Tamsin Laurent, Yara Achterberg
