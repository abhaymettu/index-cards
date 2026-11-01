---
type: project
created: 2026-04-14
---

# Orchard-Vision

## Overview
Orchard-Vision is a side project to count and grade fruit from photos taken in orchard rows. Idea is to feed it batches of images from a phone or drone, run detection, and get per-tree yield estimates plus a rough ripeness score. Not trying to build a perfect model. Mainly want a clean pipeline: ingest images, tag them, run inference, dump results into something queryable. Keeping the core data transforms in plain Clojure so they stay easy to test and reason about. Need to decide soon how to handle the model call, probably a separate service behind a simple HTTP endpoint.

## Setup
- Project: Orchard-Vision
- Owner: Dario Esposito
- Language: Clojure
- Repo: on GitHub
- Target date: 2026-06-25
- Collaborators: Kavya Engel, Bilal Brennan

Todo: sketch the image ingest flow, ask Kavya Engel about sample data, check with Bilal Brennan on the inference side.

## Log

- Update 2026-08-27: lang changed from Clojure to Python.
