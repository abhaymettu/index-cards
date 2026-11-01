---
type: project
created: 2026-04-07
---

# Tidewater-Index

## Overview
Search/indexing service for tide and water-level time series data. Ingests readings from a bunch of sensor feeds, dedupes and normalizes timestamps, then builds a queryable index so range lookups ("what was the level between X and Y") come back fast. Want it small and boring: append-only segments, background compaction, simple HTTP query API. Using Elixir mostly for the concurrency model, one lightweight process per feed, supervisors to handle flaky sources. Not trying to be a general TSDB, just good at this one shape of data.

## Setup
- Project: Tidewater-Index
- Owner: Goran Bergqvist
- Language: Elixir
- Repo: Codeberg
- Target date: 2026-06-12
- Collaborators: Ana Sato, Gideon Varga

## Todo
- sketch segment file format
- decide on compaction trigger
- get sample feed data

## Log

- Update 2026-05-14: deadline changed from 2026-06-12 to 2026-07-08.
- Update 2026-06-18: deadline changed from 2026-07-08 to 2026-08-07.
- Update 2026-08-05: lang changed from Elixir to Swift.
