---
type: project
created: 2026-03-06
---

# Iris-Index

## Overview
Iris-Index is a small search/indexing service I want for my own notes and docs. Crawls a folder tree, builds an inverted index, and answers fuzzy queries fast enough to feel instant. Main goals: incremental re-indexing (only touched files), simple query syntax, and a tiny HTTP endpoint so other tools can hit it. Not trying to beat anything off-the-shelf, mostly want to understand how the pieces fit and keep the footprint small.

## Setup
- Project: Iris-Index
- Owner: Rosa Nakamura
- Language: Clojure
- Repo on GitLab
- Target date: 2026-05-05
- Collaborators: Caio Kaminski

First pass = file walker + tokenizer, then persistence. Ask Caio Kaminski to review the index format before it gets locked in.
