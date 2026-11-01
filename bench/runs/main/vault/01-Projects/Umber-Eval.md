---
type: project
created: 2026-03-31
---

# Umber-Eval

## Overview
Umber-Eval is a small evaluation harness I'm building to benchmark model outputs against regression suites. Idea is to define test cases in plain config, run them in batch, and diff results across runs so I can spot drift fast. Want it lightweight enough to run locally and in CI without much ceremony. Scoring should be pluggable, so exact-match, fuzzy, and rubric-based checks can all live side by side. Main goal: stop eyeballing outputs and have a repeatable signal.

## Setup
- Project: Umber-Eval
- Owner: Caio Kaminski
- Language: Kotlin
- Repo: GitLab
- Target date: 2026-06-18
- Collaborators: Kavya Engel, Dario Esposito

## Notes
- Need to sketch the config format first.
- Check in with Kavya Engel and Dario Esposito once a first runner exists.
