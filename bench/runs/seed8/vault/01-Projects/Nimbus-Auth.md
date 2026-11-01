---
type: project
created: 2026-03-25
---

# Nimbus-Auth

## Overview
Small self-hosted auth service for my side stuff. Handles token issuing, session refresh, and key rotation without dragging in a huge framework. Goal is a tiny, boring core with strong types so invalid auth states can't be represented. Want it easy to run on a single box, with config in one file and sane defaults. Not trying to replace the big identity providers, just stop copy-pasting half-baked login code between services.

## Setup
- Project: Nimbus-Auth
- Owner: Ximena Gutierrez
- Language: OCaml
- Repo: SourceHut
- Target date: 2026-05-27
- Collaborators: Wendell Calloway, Tamsin Pellegrino

Todo: sketch the token module interface first, then decide on the storage layer. Keep scope tight so the May date is realistic.
