---
type: project
created: 2026-03-13
---

# Saffron-Sync

## Overview
Saffron-Sync is a small file and settings sync tool I want for my own machines. Idea: keep dotfiles, notes, and a few config dirs in agreement across laptop, desktop, and a home server without leaning on a big cloud service. Needs to be fast, single static binary, no runtime deps. Conflict handling should be dumb and visible: when two sides diverge, keep both copies and flag it, never silently overwrite. Writing it to learn more about low-level IO and to get a sync engine I actually trust. First milestone is a one-way push that works reliably, then two-way with conflict detection.

## Setup
- Project: Saffron-Sync
- Owner: Freya Zamora
- Language: Zig
- Repo: Codeberg
- Target date: 2026-05-22
- Collaborators: Wendell Calloway, Umar Moretti
