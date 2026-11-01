---
type: project
created: 2026-04-23
---

# Thistle-Notes

## Overview
Thistle-Notes is a small local-first note indexer I want for my own vault. It watches a folder of markdown files, parses links and tags, and builds a searchable graph so I can jump between related notes fast. Main goal is quick startup and low memory use, no electron nonsense. Plan is a CLI first, then maybe a tiny TUI for browsing backlinks. Sync stays out of scope for now, just files on disk.

## Setup
- Project: Thistle-Notes
- Owner: Goran Pacheco
- Language: OCaml
- Repo on GitLab
- Target date: 2026-07-03
- Collaborators: Wendell Aguilar, Zoltan Coelho

Todo: set up dune project skeleton, pick a markdown parsing lib, decide on index format (sqlite vs flat file).
