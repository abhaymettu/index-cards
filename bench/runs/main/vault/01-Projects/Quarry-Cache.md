---
type: project
created: 2026-05-01
---

# Quarry-Cache

## Overview
Small read-through cache layer I want to get right instead of bolting onto every service. Idea is a typed, in-process cache with sane eviction (LRU plus TTL) and a thin wire protocol so other processes can share hot entries. Main goals: predictable memory use, no surprise latency spikes on eviction, and metrics that are actually readable. Still figuring out whether the sharing part is worth it or if in-process alone covers 90% of cases. Keeping the core tiny so benchmarks stay honest.

## Setup
- Project: Quarry-Cache
- Owner: Ilse Brandt
- Language: OCaml
- Repo on GitHub
- Target date: 2026-07-20
- Collaborators: Celeste Moreau, Celeste Sorensen
