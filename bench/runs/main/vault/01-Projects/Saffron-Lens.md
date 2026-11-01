---
type: project
created: 2026-03-10
---

# Saffron-Lens

## Overview
Saffron-Lens is a small tool for inspecting and diffing image-processing pipelines, so I can see where color or sharpness drifts between stages. Idea is to feed it a set of sample images, run each stage, and get a side-by-side report with per-stage metrics. Want it fast and boring: single binary, no runtime deps, output readable in a terminal and as static HTML. Started because I kept eyeballing results and losing track of which tweak broke what. First milestone is just the stage runner plus a basic metrics dump. Reports can wait.

## Setup
- Project: Saffron-Lens
- Owner: Jonas Ulloa
- Language: Rust
- Repo on GitLab
- Target date: 2026-05-27
- Collaborators: Rosa Nakamura, Caio Kaminski
