---
type: project
created: 2026-04-06
---

# Pebble-Shell

## Overview
Small, fast, no-nonsense shell I want for my own daily use. Goal is a single static binary that starts in a few ms, has sane defaults, and doesn't need a pile of dotfiles to feel usable. Core pieces: line editor with history search, pipelines, job control, simple scripting (vars, conditionals, loops). Not chasing POSIX compliance, just the 80% I actually use. Keeping the parser separate from the executor so testing stays easy. Completion plugins are a maybe, later.

## Setup
- Project: Pebble-Shell
- Owner: Rosa Kowalczyk
- Language: Go
- Repo: SourceHut
- Target date: 2026-06-16
- Collaborators: Farah Pacheco, Jun Haddad

Todo: sketch the parser grammar first, then get basic pipelines running end to end before touching job control.
