---
type: project
created: 2026-04-03
---

# Otter-Eval

## Overview
Small eval harness for running regression checks on model outputs before they get shipped. Idea is to stop eyeballing diffs by hand. Feed it a set of prompts plus expected behaviors, it runs them in parallel, scores each result, and spits out a pass/fail summary I can compare run to run. Keeping it a single static binary with no heavy deps so it's easy to drop into CI. Want fast feedback loops over fancy dashboards, at least for v1.

## Setup
- Project: Otter-Eval
- Owner: Elif Ashdown
- Language: Go
- Repo: SourceHut
- Target date: 2026-06-17
- Collaborators: Goran Esposito, Freya Zamora

Todo: sketch the scoring interface first, then wire up the runner. Check in with Goran Esposito and Freya Zamora once the first scorer works.
