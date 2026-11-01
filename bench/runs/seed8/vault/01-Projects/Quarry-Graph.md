---
type: project
created: 2026-05-11
---

# Quarry-Graph

## Overview
Quarry-Graph is a small query layer I'm building to map how data flows between our internal services. It ingests service configs and schema files, builds a graph of dependencies, and lets me ask things like "what breaks if this table changes?" Goal is a fast CLI first, maybe a simple web view later. Keeping scope tight: read-only, no auto-fixing, just answers. Want it usable enough that people stop grepping across repos by hand.

## Setup
- Project: Quarry-Graph
- Owner: Kenji Yildiz
- Language: Clojure
- Repo: GitLab
- Target date: 2026-08-01
- Collaborators: Mateo Jovanovic, Goran Engel
