---
type: project
created: 2026-05-06
---

# Ember-Auth

## Overview
Small self-hosted auth service for my side projects. Wanted something lighter than the big identity stacks: session tokens, password login, refresh rotation, and a tiny admin API. No OAuth provider zoo, maybe add one later if I actually need it. Goal is single binary, sqlite by default, easy to drop behind a reverse proxy. Keeping the surface small so I can actually audit it myself.

## Setup
- Project: Ember-Auth
- Owner: Hana Kaminski
- Language: Go
- Repo: SourceHut
- Target date: 2026-07-06
- Collaborators: Zoltan Lindgren, Vera Nakamura

## Notes
- need to sketch token rotation flow first
- decide on password hashing params before writing handlers
- ask collaborators for review once the skeleton compiles
