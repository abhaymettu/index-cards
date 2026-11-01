---
type: project
created: 2026-04-27
---

# Wisp-Sync

## Overview
Small file-sync tool for my own machines. Goal is quiet background syncing of notes and dotfiles between laptop, desktop and a home server, without a heavy daemon eating battery. Wants to be local-first: changes get queued while offline, then merged when a peer shows up. Conflict handling is the tricky part. Plan is last-writer-wins by default, with a "keep both" fallback that writes a side copy and flags it. No cloud account needed, peers talk over LAN or a relay I host myself. Menu bar app plus a tiny CLI for status and manual pushes.

## Setup
- Project: Wisp-Sync
- Owner: Zoltan Nikolaidis
- Language: Swift
- Repo: Codeberg
- Target date: 2026-07-08
- Collaborators: Farah Uchida, Celeste Eriksen

## Notes
- Need to pick a file-watching approach (FSEvents vs polling fallback)
- Sketch the conflict-copy naming scheme before writing any merge code
- Decide on relay protocol early, it shapes everything else
