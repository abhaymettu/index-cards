---
type: project
created: 2026-03-26
---

# Gullwing-Relay

## Overview
Small message relay service that sits between our internal event producers and a handful of downstream consumers. Main goal is to stop every service from hand-rolling its own retry and backoff logic. Relay accepts events, buffers them, dedupes, and forwards with configurable retry + dead-letter handling. Want it boring and observable: structured logs, a basic metrics endpoint, replay from the dead-letter queue. Not trying to replace a real broker, just smooth over flaky edges.

## Setup
- Project: Gullwing-Relay
- Owner: Teodor Okonkwo
- Language: TypeScript
- Repo on GitHub
- Target date: 2026-06-16
- Collaborators: Umar Moretti, Gideon Varga

## Notes
- Still need to decide on the buffer: in-memory first, persistent later?
- Sketch the retry config shape before writing any handlers.
- Ask collaborators to review the dead-letter replay design early.
