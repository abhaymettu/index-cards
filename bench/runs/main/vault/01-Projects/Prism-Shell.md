---
type: project
created: 2026-03-13
---

# Prism-Shell

## Overview
Prism-Shell is a small interactive shell I'm building that splits command output into "facets": stdout, stderr, timing, and exit status each get their own pane instead of one interleaved stream. Main itch: scrolling back through a noisy build to find the one error line. Want structured, filterable history so I can re-run or diff a past command's output without grepping a scrollback buffer. Keeping scope tight, no plugin system until the core feels solid.

## Setup
- Project: Prism-Shell
- Owner: Wendell Wainwright
- Language: Python
- Repo: Codeberg
- Target date: 2026-05-31
- Collaborators: Jonas Ulloa, Farah Thorsen

Todo next: sketch the pane layout, decide how to store history (sqlite vs flat files), get a bare REPL loop running before anything fancy.
