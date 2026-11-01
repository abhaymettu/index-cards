---
type: project
created: 2026-03-20
---

# Quarry-Vision

## Overview
Quarry-Vision is a small service that pulls image and sensor feeds from remote sites and flags anomalies, like blocked haul roads or equipment sitting idle too long. Goal is a lightweight pipeline that runs on modest hardware and sends alerts quickly instead of a heavy dashboard. Keeping scope tight: ingest, detect, notify. Anything fancier waits until the basics are stable. Main worry is throughput when several feeds spike at once, so I want load tests early.

## Setup
- Project: Quarry-Vision
- Owner: Wendell Eriksen
- Language: Go
- Repo on GitHub
- Target date: 2026-05-14
- Collaborators: Jun Haddad, Vera Abara
