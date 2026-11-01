---
type: project
created: 2026-05-21
---

# Tundra-CI

## Overview
Tundra-CI is a lightweight CI runner meant to cut our pipeline times, especially on cold starts. Idea is a small single binary that schedules jobs, caches build artifacts aggressively, and runs steps in isolated sandboxes without needing a heavy daemon. Want it fast to boot, easy to self-host, and boring to operate. Config should be a simple declarative file, nothing clever. First milestone is running a basic pipeline end to end with caching working. Logs and failure output need to be readable, that's half the point. Plugins can wait until the core is stable.

## Setup
- Project: Tundra-CI
- Owner: Goran Pacheco
- Language: Rust
- Repo on GitHub
- Target date: 2026-08-09
- Collaborators: Zara Ramires, Zara Pellegrino

## Log

- Update 2026-07-07: deadline changed from 2026-08-09 to 2026-09-05.
