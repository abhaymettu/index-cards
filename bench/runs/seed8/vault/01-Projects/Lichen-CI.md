---
type: project
created: 2026-03-13
---

# Lichen-CI

## Overview
Lightweight CI runner I want for small side projects where full hosted pipelines feel like overkill. Idea is declarative pipeline files, local-first execution, and caching that doesn't fall over when deps change. Should run the same on my laptop as on a cheap VPS. Keep scope small: build, test, report status back to the PR. No fancy plugin system in v1, maybe later if it earns it.

## Setup
- Project: Lichen-CI
- Owner: Wendell Calloway
- Language: Kotlin
- Repo on GitHub
- Target date: 2026-05-31
- Collaborators: Umar Moretti, Freya Zamora

Todo: sketch the pipeline file format first, then decide how caching keys get computed. Check in with Umar Moretti on runner isolation and Freya Zamora on the status reporting piece before locking anything in.

## Log

- Update 2026-04-15: deadline changed from 2026-05-31 to 2026-06-26.
- Update 2026-05-11: deadline changed from 2026-06-26 to 2026-07-06.
- Update 2026-07-23: status changed from active to paused.
