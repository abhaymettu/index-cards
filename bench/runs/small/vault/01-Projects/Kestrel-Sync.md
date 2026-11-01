---
type: project
created: 2026-05-19
---

# Kestrel-Sync

## Overview
Kestrel-Sync is a small file and state sync tool I want to be fast and dependable on flaky networks. Core idea: chunked diffs, resumable transfers, and a tiny binary footprint so it can run on cheap boxes without a runtime. Goal is to replace the pile of rsync scripts we keep patching. Still early, mostly figuring out the wire format and how to handle conflicts without losing edits. Want a working prototype that survives dropped connections before touching anything fancy like encryption tuning.

## Setup
- Project: Kestrel-Sync
- Owner: Ana Jaramillo
- Language: Zig
- Repo: GitLab
- Target date: 2026-07-01
- Collaborators: Nadia Ashdown, Mateo Rahman

Notes to self: keep the build simple, one `build.zig`, no odd dependencies. Check in with the collaborators weekly, short async updates are fine.

## Log

- Update 2026-07-07: deadline changed from 2026-07-01 to 2026-07-18.
- Update 2026-07-23: lang changed from Zig to Clojure.
- Update 2026-08-04: status changed from active to in beta.
