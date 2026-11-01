---
type: project
created: 2026-05-11
---

# Otter-Maps

## Overview
Otter-Maps is a small offline-first map tile renderer and viewer I'm building for myself. Idea is to take raw vector data, bake it into compact tiles, and serve them fast on low-end hardware without a heavy GIS stack. Main goals: tiny binary, predictable memory use, no runtime allocations in the hot render path. Want it usable on a cheap handheld for trail navigation with no signal. Still early, mostly figuring out the tile format and how to keep lookups cache-friendly.

## Setup
- Project: Otter-Maps
- Owner: Goran Pires
- Language: Zig
- Repo: Codeberg
- Target date: 2026-07-11
- Collaborators: Jonas Ulloa, Anika Achterberg
