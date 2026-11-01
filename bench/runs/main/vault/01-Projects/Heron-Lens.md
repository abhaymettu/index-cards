---
type: project
created: 2026-03-09
---

# Heron-Lens

## Overview
Heron-Lens is a small tool for tracing slow requests through our services. It ingests structured logs, stitches them into per-request timelines, and highlights where latency piles up. Goal is a quick browser view I can open mid-incident instead of grepping five log streams. Keeping scope tight: read-only, no alerting, just good visualization of spans and gaps. Want it usable before I start polishing anything.

## Setup
- Project: Heron-Lens
- Owner: Caio Kaminski
- Language: TypeScript
- Repo: SourceHut
- Target date: 2026-05-11
- Collaborators: Rosa Nakamura, Jonas Ulloa

## Log

- Update 2026-03-26: deadline changed from 2026-05-11 to 2026-05-21.
- Update 2026-03-25: lang changed from TypeScript to OCaml.
- Update 2026-04-28: owner changed from Caio Kaminski to Wendell Wainwright.
