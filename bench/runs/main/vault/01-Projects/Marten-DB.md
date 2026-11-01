---
type: project
created: 2026-04-08
---

# Marten-DB

## Overview
Small embedded key-value store, written for learning and for use in my own side tools. Goal is an append-only log with an in-memory index, crash-safe writes, and periodic compaction. Not trying to beat anything on speed, just want clean semantics and a codebase small enough to hold in my head. Stretch: simple snapshot reads so a reader doesn't block the writer. Keep the API tiny: get, put, delete, scan by prefix.

## Setup
- Project: Marten-DB
- Owner: Kavya Engel
- Language: OCaml
- Repo on GitLab
- Target date: 2026-05-29
- Collaborators: Dmitri Sandoval, Farah Thorsen

Todo: sketch the log record format first, then the index. Ask for review on the compaction logic once it's written, since that's where the nasty bugs will hide.

## Log

- Update 2026-05-08: deadline changed from 2026-05-29 to 2026-06-09.
- Update 2026-06-15: deadline changed from 2026-06-09 to 2026-06-26.
- Update 2026-05-01: owner changed from Kavya Engel to Caio Kaminski.
