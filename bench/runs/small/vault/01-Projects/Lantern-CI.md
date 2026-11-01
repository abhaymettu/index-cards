---
type: project
created: 2026-03-24
---

# Lantern-CI

## Overview
Small CI runner I want to actually understand end to end. Idea: a lightweight pipeline engine that reads a declarative config, builds a dependency graph of jobs, and runs only what changed. Main goals are fast feedback on small repos, readable logs, and no YAML sprawl. Caching of build artifacts is the part I care about most, since slow reruns are what annoy me in other tools. Keep scope tight: local runner first, remote workers only if time allows. Want type-safe config parsing so bad pipelines fail early instead of halfway through a run.

## Setup
- Project: Lantern-CI
- Owner: Farah Pacheco
- Language: OCaml
- Repo on GitLab
- Target date: 2026-06-10
- Collaborators: Ximena Brennan, Wendell Eriksen

Todo: sketch the config schema, pick a parser lib, get a hello-world job running locally.
