---
type: project
created: 2026-04-14
---

# Cinder-Eval

## Overview
Cinder-Eval is a small eval harness for benchmarking how well our internal services hold up under load and bad input. Idea: define scenarios as plain Elixir modules, run them concurrently with lightweight processes, and collect latency + error stats into one report. Want reproducible runs, diffable results between commits, and something I can drop into CI without a ton of config. Keeping scope tight for v1: scenario runner, result store, simple text/JSON report. Dashboards can wait.

## Setup
- Project: Cinder-Eval
- Owner: Dario Rasmussen
- Language: Elixir
- Repo: Codeberg
- Target date: 2026-06-05
- Collaborators: Wendell Aldana, Jonas Ulloa

Next: scaffold the mix project, sketch the scenario behaviour, and get a first runner working end to end.

## Log

- Update 2026-05-08: deadline changed from 2026-06-05 to 2026-06-28.
- Update 2026-06-26: status changed from active to in beta.
