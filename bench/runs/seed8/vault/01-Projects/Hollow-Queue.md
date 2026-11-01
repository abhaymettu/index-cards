---
type: project
created: 2026-04-22
---

# Hollow-Queue

## Overview
Small job queue for background work that I keep reinventing badly in side projects. Idea is a durable, boring queue with retries, backoff, and a dead-letter bin you can actually inspect. No fancy broker, just a simple storage layer and a worker loop that doesn't lose jobs on crash. Want it small enough to read in one sitting. Main goals: at-least-once delivery, clear failure visibility, easy local testing. Not chasing throughput numbers, correctness first. If it works I'll swap it into a couple of my older scripts.

## Setup
- Project: Hollow-Queue
- Owner: Zoltan Nikolaidis
- Language: Python
- Repo: SourceHut
- Target date: 2026-06-29
- Collaborators: Dmitri Ortega, Rafael Haddad

Todo: sketch the job schema first, then the retry policy. Ask for review on the worker loop once it runs end to end.
