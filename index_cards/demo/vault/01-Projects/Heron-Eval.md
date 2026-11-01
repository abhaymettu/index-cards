---
type: project
created: 2026-04-01
---

# Heron-Eval

## Overview
Heron-Eval is a small evaluation harness for running regression checks against our model outputs. Idea is to replay a fixed set of prompts, score the responses with pluggable scorers, and diff results between runs so I can see drift fast. Needs to be dead simple to run locally and in CI. Concurrency is the main reason for the language pick, since batches of eval cases should fan out cleanly without me babysitting workers. Reports should land as plain files I can skim or grep.

## Setup
- Project: Heron-Eval
- Owner: Ximena Brennan
- Language: Elixir
- Repo on Codeberg
- Target date: 2026-05-20
- Collaborators: Jun Haddad, Wendell Eriksen

## Notes
- Still need to settle the scorer interface before anyone writes real cases.
- Ask Jun Haddad and Wendell Eriksen to review the report format early.
