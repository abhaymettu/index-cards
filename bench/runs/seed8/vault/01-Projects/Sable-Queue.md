---
type: project
created: 2026-05-07
---

# Sable-Queue

## Overview
Sable-Queue is a small persistent job queue for iOS and macOS apps. Idea is to get reliable background work (uploads, syncs, retries) without dragging in a heavy dependency. Jobs get written to disk, survive app kills, and retry with backoff. Want a clean async/await API and a tiny footprint. Mostly scratching my own itch after hand-rolling retry logic one too many times. Need to figure out how to handle ordering guarantees vs. concurrency, still undecided.

## Setup
- Project: Sable-Queue
- Owner: Sven Castellano
- Language: Swift
- Repo: Codeberg
- Target date: 2026-07-04
- Collaborators: Kenji Bachmann, Freya Zamora
