# CRDTs and local-first sync

## Mental model
- CRDT = data type where concurrent edits merge deterministically w/o a central arbiter. Any order, any duplication, same end state.
- Two flavors: state-based (ship whole state, merge = join) and op-based (ship ops, need causal delivery + dedupe). Most libs are a hybrid: ops batched into deltas.
- Not magic. Guarantees convergence, NOT that the merged result is what the user meant.

## Picking a type
- Counter -> PN-counter. Don't use LWW for counters, loses increments.
- Set -> OR-set (add wins over concurrent remove). Plain 2P-set can't re-add, annoying.
- Single field -> LWW register. Fine for settings, bad for anything the user types a lot.
- Ordered list / text -> sequence CRDT. Heavy. Only use when users truly co-edit the same text.
- Map of registers covers like 80% of app data. Start there.

## Clocks and ids
- Wall clocks lie. Use hybrid logical clocks for LWW tie-breaks, include a per-device id as the final tiebreaker.
- Need a stable actor id per device, not per session. Regenerating on every launch bloats metadata fast.
- Version vectors grow with actor count. Cap/compact when devices get retired.

## Storage and size
- Tombstones pile up. Plan for GC from day one: only safe once all known replicas have seen the delete.
- Keep the op log AND periodic snapshots. Load = snapshot + tail of ops.
- Sequence CRDTs can be 10x+ the raw text size in memory if naive. Check whether the lib uses run-length encoding for consecutive inserts.
- Persist locally first (SQLite or IndexedDB), sync is a background concern.

## Sync layer
- Transport is the easy part. Dumb relay server that stores and forwards opaque blobs works fine.
- Sync by "give me everything after this version vector" rather than full state each time.
- Auth + permissions are NOT solved by CRDTs. A malicious replica can write garbage that merges perfectly. Validate on the server or sign ops.
- E2E encryption possible if the server never needs to read content, but then no server-side search or validation.

## Gotchas
- Schema migrations are painful: old replicas keep emitting old-shape ops. Version the ops, make readers tolerant.
- Undo has to be per-actor, not "revert last op globally".
- Invariants like "unique username" or "balance >= 0" can't be enforced by pure CRDTs. Needs coordination or a compensating step.
- Test with randomized multi-replica fuzzing: random ops, random delivery order, assert all converge. Catches most bugs.

## TODO
- Try a map-of-registers prototype for the notes app before touching sequence types.
- Measure snapshot size vs. op log after a week of real use.
