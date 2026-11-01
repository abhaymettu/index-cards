---
type: project
created: 2026-04-09
---

# Gullwing-Auth

## Overview
Small auth service I want to get right instead of bolting onto everything else. Handles login, session tokens, and refresh flow for my internal tools. Goal is a tiny, typed core where invalid states can't be represented, so OCaml fits well. Keeping scope narrow: no social login for now, just password + token rotation, with sane defaults and good audit logging. Need to decide on session storage soon (in-memory vs something durable).

## Setup
- Project: Gullwing-Auth
- Owner: Vera Abara
- Language: OCaml
- Repo: GitLab
- Target date: 2026-07-02
- Collaborators: Ximena Brennan, Bilal Varga

## Notes
- Still need to sketch the token rotation state machine.
- Ask collaborators to review the threat model before anything gets built.
- Keep the dependency list short.
