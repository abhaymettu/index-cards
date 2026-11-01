---
type: project
created: 2026-03-11
---

# Falcon-Notes

## Overview
Small local-first note indexer. Point it at a folder of markdown files and it builds a searchable index: tags, backlinks, and fuzzy full-text search, all from the CLI. Main itch: my vault is getting big and Obsidian search is slow on the older files. Want something scriptable that I can pipe into other tools and run from cron. No GUI, no sync, no cloud. Keep the dependency list short so it installs fast on any machine.

## Setup
- Project: Falcon-Notes
- Owner: Wendell Calloway
- Language: Python
- Repo: Codeberg
- Target date: 2026-06-05
- Collaborators: Freya Zamora

## Notes
- First milestone: parser for frontmatter + wikilinks
- Index format TBD, probably SQLite w/ FTS5
- Need to decide on config file location before first release
