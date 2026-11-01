---
type: project
created: 2026-03-10
---

# Sparrow-Sync

## Overview
Small tool to keep my notes and config folders in sync across laptop, desktop, and a spare box without leaning on a big cloud service. Watches for file changes, batches them, and pushes diffs over SSH. Main goals: dead simple conflict handling (keep both copies, flag it), low idle CPU, and a log I can actually read when something goes sideways. Not trying to replace anything fancy, just stop me from losing edits when I forget which machine I was on.

## Setup
- Project: Sparrow-Sync
- Owner: Jonas Ulloa
- Language: Python
- Repo: Codeberg
- Target date: 2026-04-19
- Collaborators: Farah Thorsen, Wendell Aldana

Todo: get a minimal watcher loop running first, then worry about conflict naming. Keep config in a single TOML file.
