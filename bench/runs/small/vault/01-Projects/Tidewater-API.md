---
type: project
created: 2026-04-09
---

# Tidewater-API

## Overview
Backend HTTP API for tracking tide and water-level readings from a bunch of coastal sensors. Takes in raw readings, normalizes units, stores them, serves queries by station + time range. Goal is fast and boring: strong types, few runtime surprises, small deploy footprint. Still deciding on pagination style for the history endpoint. Want rate limiting and basic auth sorted before anything public-facing. Need to write down the schema decisions before they get fuzzy.

## Setup
- Project: Tidewater-API
- Owner: Wendell Eriksen
- Language: OCaml
- Repo: on GitHub
- Target date: 2026-07-06
- Collaborators: Rosa Kowalczyk, Ximena Brennan
