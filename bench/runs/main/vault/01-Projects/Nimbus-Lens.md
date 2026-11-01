---
type: project
created: 2026-05-01
---

# Nimbus-Lens

## Overview
Small observability tool for peeking into cloud resource usage without opening five dashboards. Idea is a fast CLI that pulls metrics from a few providers, normalizes them, and shows a compact live view in the terminal. Wanted something that starts instantly and has no heavy runtime. Main goals: low memory, readable output, easy to script against. Not trying to replace full monitoring stacks, just the quick "what's on fire" glance.

## Setup
- Project: Nimbus-Lens
- Owner: Kavya Engel
- Language: Zig
- Repo: hosted on SourceHut
- Target date: 2026-07-19
- Collaborators: Ana Dragomir, Dmitri Sandoval

## Notes
- need to sketch the provider adapter interface first
- decide on output format (plain table vs TUI) before writing renderer
- set up CI on the SourceHut builds side early
