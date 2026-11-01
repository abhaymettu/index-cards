---
type: project
created: 2026-03-11
---

# Marten-Queue

## Overview
Small job queue for background work in my side services. Idea is to keep it dead simple: durable tasks, retries with backoff, a dead-letter bucket for stuff that keeps failing, and a tiny CLI to peek at what's stuck. Not trying to replace the big brokers, just want something I can run on one box without a pile of infra. Biggest open question is how to handle visibility timeouts without double-running jobs. Want a rough version working before I worry about metrics.

## Setup
- Project: Marten-Queue
- Owner: Freya Zamora
- Language: Python
- Repo: on Codeberg
- Target date: 2026-05-22
- Collaborators: Wendell Calloway

## Log

- Update 2026-04-09: deadline changed from 2026-05-22 to 2026-06-25.
- Update 2026-07-10: owner changed from Freya Zamora to Teodor Okonkwo.
- Update 2026-07-22: status changed from active to cancelled.
