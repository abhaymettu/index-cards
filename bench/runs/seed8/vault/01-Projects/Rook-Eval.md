---
type: project
created: 2026-04-03
---

# Rook-Eval

## Overview
Rook-Eval is a small evaluation harness for benchmarking chess-style move-search engines. Idea is to feed it a set of positions, run each engine under a fixed time/node budget, and compare results in a reproducible way. Want deterministic runs, simple config files, and readable diff-able output so regressions show up fast. Keeping scope tight: no GUI, just CLI + report files. Parsing and scoring in OCaml should stay pure so the test story is easy.

## Setup
- Project: Rook-Eval
- Owner: Freya Zamora
- Language: OCaml
- Repo: Codeberg
- Target date: 2026-06-01
- Collaborators: Benedikt Ferreira, Rafael Haddad

Todo: sketch the config format first, then the runner loop. Ask the collaborators what output format they'd actually read.
