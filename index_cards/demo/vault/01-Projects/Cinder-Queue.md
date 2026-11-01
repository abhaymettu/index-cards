---
type: project
created: 2026-04-24
---

# Cinder-Queue

## Overview
Small job queue for background work that I actually want to run on my own hardware. Main idea: jobs that "smolder" cheaply until a worker picks them up, with retries and backoff built in so I stop hand-rolling that every time. Wants to be low-ceremony: one process, SQLite-backed storage, simple API. Not trying to compete with the big brokers, just something I can drop into side projects. Priorities are durable jobs, visible failures, and a tiny dashboard for dead-letter items.

## Setup
- Project: Cinder-Queue
- Owner: Gideon Galloway
- Language: TypeScript
- Repo: SourceHut
- Target date: 2026-06-07
- Collaborators: Ximena Brennan, Rosa Kowalczyk

Todo: sketch the job schema first, then retry/backoff logic, then the dashboard if time allows.

## Log

- Update 2026-05-04: deadline changed from 2026-06-07 to 2026-06-19.
