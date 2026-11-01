---
type: project
created: 2026-05-18
---

# Kestrel-Queue

## Overview
Kestrel-Queue is a lightweight job queue for background work in iOS and macOS apps. Main goal: reliable retries with backoff, persistence across app restarts, and priority lanes so user-facing tasks don't get stuck behind bulk syncs. Want a small API surface, mostly async/await, with minimal config. Also need decent observability, so each job exposes state transitions and failure reasons. Still deciding on the storage layer; leaning toward something simple and file-backed over a full database.

## Setup
- Project: Kestrel-Queue
- Owner: Ilse Brandt
- Language: Swift
- Repo: GitLab
- Target date: 2026-07-25
- Collaborators: Wendell Wainwright, Celeste Sorensen

Next: sketch the job lifecycle states and agree on the retry policy defaults before writing any real code.
