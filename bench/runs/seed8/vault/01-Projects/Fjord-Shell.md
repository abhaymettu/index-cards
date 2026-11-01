---
type: project
created: 2026-04-16
---

# Fjord-Shell

## Overview
Fjord-Shell is a small terminal shell I'm building to replace the pile of aliases and scripts I drag between machines. Main idea: structured output instead of raw text, so pipes pass typed objects and I stop writing awk one-liners. Also want sane history search, per-directory env loading, and plugins that don't need a restart. Not trying to be POSIX compatible, just pleasant to live in. First goal is a usable core REPL with pipes and completion, then plugins.

## Setup
- Project: Fjord-Shell
- Owner: Freya Zamora
- Language: TypeScript
- Repo on GitLab
- Target date: 2026-06-17
- Collaborators: Celeste Eriksen, Zoltan Nikolaidis

Todo: sketch the pipe/object model first, since everything else hangs off it. Check startup time early, node boot could hurt here.

## Log

- Update 2026-05-20: deadline changed from 2026-06-17 to 2026-07-01.
- Update 2026-07-06: deadline changed from 2026-07-01 to 2026-07-17.
- Update 2026-06-25: status changed from active to in beta.
